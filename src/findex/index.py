"""Інвертований індекс, який будується за один прохід потоку документів."""

from __future__ import annotations

import argparse
import time
import tracemalloc
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from itertools import islice
from pathlib import Path

from findex.corpus import Document, iter_documents
from findex.instrument import timed
from findex.tokenize import tokenize


@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    tf: int
    positions: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class DocMeta:
    path: str
    title: str
    text: str


@dataclass(eq=False)
class Index:
    postings: dict[str, Sequence[Posting]]
    doc_lengths: dict[int, int]
    doc_meta: dict[int, DocMeta]
    positions: bool = False
    closed: bool = field(default=False, init=False)

    def __getitem__(self, term: str) -> Sequence[Posting]:
        if self.closed:
            raise ValueError("Індекс закрито")
        return self.postings[term]

    def __iter__(self) -> Iterator[str]:
        return iter(self.postings)

    def __len__(self) -> int:
        return len(self.postings)

    def __contains__(self, term: object) -> bool:
        return term in self.postings

    def __repr__(self) -> str:
        return f"Index(documents={self.num_docs}, terms={len(self)}, positions={self.positions})"

    @property
    def num_docs(self) -> int:
        return len(self.doc_meta)

    @cached_property
    def avg_doc_length(self) -> float:
        return sum(self.doc_lengths.values()) / self.num_docs if self.num_docs else 0.0

    def doc_length(self, doc_id: int) -> int:
        return self.doc_lengths[doc_id]

    def df(self, term: str) -> int:
        return len(self.postings.get(term, []))

    def close(self) -> None:
        import sys

        from findex.search import candidate_ids

        candidate_ids.cache_clear()
        if "findex.vector" in sys.modules:
            from findex.vector import vector_index

            vector_index.cache_clear()
        if "findex.semantic" in sys.modules:
            from findex.semantic import get_semantic

            get_semantic.cache_clear()
        self.closed = True


@timed
def build_index(documents: Iterable[Document], *, positions: bool = False) -> Index:
    postings: defaultdict[str, list[Posting]] = defaultdict(list)
    lengths: dict[int, int] = {}
    metadata: dict[int, DocMeta] = {}
    for doc in documents:
        if doc.doc_id in lengths:
            raise ValueError(f"Повторний doc_id: {doc.doc_id}")
        offsets: defaultdict[str, list[int]] = defaultdict(list)
        length = 0
        for offset, term in enumerate(tokenize(doc.text)):
            offsets[term].append(offset)
            length += 1
        for term, values in offsets.items():
            postings[term].append(
                Posting(doc.doc_id, len(values), tuple(values) if positions else ())
            )
        lengths[doc.doc_id] = length
        metadata[doc.doc_id] = DocMeta(doc.path, doc.title or doc.path, doc.text)
    for posting_list in postings.values():
        posting_list.sort(key=lambda p: p.doc_id)
    return Index(dict(postings), lengths, metadata, positions)


def main() -> None:
    from findex.store import save

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--out", type=Path, default=Path("index.bin"))
    parser.add_argument("--positions", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    tracemalloc.start()
    started = time.perf_counter()
    index = build_index(islice(iter_documents(args.corpus), args.limit), positions=args.positions)
    save(index, args.out)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(
        f"documents={len(index.doc_meta)} terms={len(index.postings)} "
        f"elapsed_s={time.perf_counter() - started:.6f} peak_bytes={peak}"
    )


if __name__ == "__main__":
    main()
