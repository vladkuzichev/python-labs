"""Справжнє зберігання int32 та векторизовані TF-IDF/BM25 без циклу за Posting."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, overload

import numpy as np
from numpy.typing import NDArray

from findex.boolean import Engine
from findex.index import DocMeta, Index, Posting
from findex.query import parse
from findex.search import SearchResult, candidate_ids, snippet

IntArray = NDArray[np.int32]
FloatArray = NDArray[np.float64]
ScorerName = Literal["bm25", "tfidf"]


class PackedPostings(Sequence[Posting]):
    def __init__(
        self, doc_ids: IntArray, tfs: IntArray, positions: IntArray, offsets: IntArray
    ) -> None:
        self.doc_ids = doc_ids
        self.tfs = tfs
        self.positions = positions
        self.offsets = offsets

    def __len__(self) -> int:
        return self.doc_ids.size

    @overload
    def __getitem__(self, item: int) -> Posting: ...
    @overload
    def __getitem__(self, item: slice) -> list[Posting]: ...
    def __getitem__(self, item: int | slice) -> Posting | list[Posting]:
        if isinstance(item, slice):
            return [self[i] for i in range(*item.indices(len(self)))]
        i = item if item >= 0 else len(self) + item
        if i < 0 or i >= len(self):
            raise IndexError(item)
        start, end = int(self.offsets[i]), int(self.offsets[i + 1])
        return Posting(
            int(self.doc_ids[i]), int(self.tfs[i]), tuple(int(p) for p in self.positions[start:end])
        )


def pack(postings: Sequence[Posting]) -> PackedPostings:
    ids = np.fromiter((p.doc_id for p in postings), dtype=np.int32, count=len(postings))
    tfs = np.fromiter((p.tf for p in postings), dtype=np.int32, count=len(postings))
    offsets = np.zeros(len(postings) + 1, dtype=np.int32)
    position_list: list[int] = []
    for i, p in enumerate(postings):
        position_list.extend(p.positions)
        offsets[i + 1] = len(position_list)
    return PackedPostings(ids, tfs, np.asarray(position_list, dtype=np.int32), offsets)


class VectorIndex:
    def __init__(self, index: Index) -> None:
        self.ids = np.asarray(sorted(index.doc_meta), dtype=np.int32)
        self.doc_len = np.asarray([index.doc_lengths[int(i)] for i in self.ids], dtype=np.int32)
        self.postings = {
            term: values if isinstance(values, PackedPostings) else pack(values)
            for term, values in index.postings.items()
        }


@lru_cache(maxsize=8)
def vector_index(index: Index) -> VectorIndex:
    return VectorIndex(index)


def top_k(ids: IntArray, scores: FloatArray, k: int) -> IntArray:
    """Argpartition із детермінованим розв’язанням нічиїх за найменшим doc_id."""
    if ids.size == 0:
        return np.empty(0, dtype=np.int32)
    values = np.round(scores, 12)
    count = min(k, ids.size)
    if count < ids.size:
        selected = np.argpartition(-values, count - 1)[:count]
        threshold = float(values[selected].min())
        above = np.flatnonzero(values > threshold)
        tied = np.flatnonzero(values == threshold)
        tied = tied[np.argsort(ids[tied], kind="stable")][: count - above.size]
        selected = np.concatenate((above, tied))
    else:
        selected = np.arange(ids.size)
    order = np.lexsort((ids[selected], -values[selected]))
    return np.asarray(selected[order], dtype=np.int32)


def search_numpy(
    index: Index,
    query: str,
    *,
    scorer: ScorerName = "bm25",
    k: int = 10,
    with_snippets: bool = True,
    engine: Engine = "merge",
) -> list[SearchResult]:
    if k < 1:
        raise ValueError("k має бути додатним")
    view = vector_index(index)
    allowed = np.asarray(candidate_ids(index, query, engine), dtype=np.int32)
    if allowed.size == 0:
        return []
    scores = np.zeros(view.ids.size, dtype=np.float64)
    terms = tuple(dict.fromkeys(parse(query).terms()))
    for term in terms:
        postings = view.postings.get(term)
        if postings is None or not len(postings):
            continue
        rows = np.searchsorted(view.ids, postings.doc_ids)
        tf = postings.tfs.astype(np.float64)
        df = len(postings)
        if scorer == "bm25":
            idf = math.log(1.0 + (index.num_docs - df + 0.5) / (df + 0.5))
            norm = 1 - 0.75 + 0.75 * view.doc_len[rows] / (index.avg_doc_length or 1)
            weights = idf * tf * 2.5 / (tf + 1.5 * norm)
        else:
            weights = (1 + np.log(tf)) * math.log(1 + index.num_docs / df)
        scores[rows] += weights
    allowed_rows = np.searchsorted(view.ids, allowed)
    selected = top_k(allowed, scores[allowed_rows], k)
    return [
        SearchResult(
            int(allowed[i]),
            float(scores[allowed_rows[i]]),
            index.doc_meta[int(allowed[i])].title,
            snippet(index.doc_meta[int(allowed[i])].text, terms) if with_snippets else "",
        )
        for i in selected
    ]


def save_numpy(index: Index, path: Path) -> None:
    """NPZ містить лише числові масиви та JSON-рядок; allow_pickle=False під час читання."""
    terms = sorted(index.postings)
    buffers: dict[str, list[IntArray]] = {
        name: [] for name in ["doc_ids", "tfs", "positions", "offsets"]
    }
    term_offsets = [0]
    position_offset = 0
    for term in terms:
        p = index.postings[term]
        packed = p if isinstance(p, PackedPostings) else pack(p)
        for name in ["doc_ids", "tfs", "positions"]:
            buffers[name].append(getattr(packed, name))
        buffers["offsets"].append(packed.offsets[:-1] + position_offset)
        position_offset += packed.positions.size
        term_offsets.append(term_offsets[-1] + len(packed))
    metadata = {
        "terms": terms,
        "positions": index.positions,
        "lengths": index.doc_lengths,
        "documents": {
            str(i): {"path": m.path, "title": m.title, "text": m.text}
            for i, m in index.doc_meta.items()
        },
    }
    arrays: dict[str, Any] = {
        name: np.concatenate(parts) if parts else np.empty(0, dtype=np.int32)
        for name, parts in buffers.items()
    }
    arrays["offsets"] = np.append(arrays["offsets"], np.int32(position_offset))
    arrays["term_offsets"] = np.asarray(term_offsets, dtype=np.int32)
    arrays["doc_len"] = np.asarray(list(index.doc_lengths.values()), dtype=np.int32)
    arrays["metadata"] = np.array(json.dumps(metadata, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def load_numpy(path: Path) -> Index:
    with np.load(path, allow_pickle=False) as archive:
        data = json.loads(str(archive["metadata"]))
        ids = np.asarray(archive["doc_ids"], dtype=np.int32)
        tfs = np.asarray(archive["tfs"], dtype=np.int32)
        positions = np.asarray(archive["positions"], dtype=np.int32)
        offsets = np.asarray(archive["offsets"], dtype=np.int32)
        term_offsets = np.asarray(archive["term_offsets"], dtype=np.int32)
        postings: dict[str, Sequence[Posting]] = {}
        for i, term in enumerate(data["terms"]):
            start, end = int(term_offsets[i]), int(term_offsets[i + 1])
            pos_start, pos_end = int(offsets[start]), int(offsets[end])
            postings[term] = PackedPostings(
                ids[start:end],
                tfs[start:end],
                positions[pos_start:pos_end],
                offsets[start : end + 1] - pos_start,
            )
        return Index(
            postings,
            {int(i): n for i, n in data["lengths"].items()},
            {int(i): DocMeta(**m) for i, m in data["documents"].items()},
            data["positions"],
        )
