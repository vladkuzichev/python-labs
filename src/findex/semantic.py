"""MiniLM ONNX, справжні ембеддинги фрагментів, cosine та Reciprocal Rank Fusion."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from findex.index import Index
from findex.search import SearchResult, snippet
from findex.tokenize import tokenize
from findex.vector import top_k

Embedding = NDArray[np.float32]
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


class MiniLM:
    def __init__(self, model_path: Path) -> None:
        if not (model_path / "model_quint8_avx2.onnx").is_file():
            raise FileNotFoundError(f"Модель MiniLM не знайдено: {model_path}")
        # ONNX Runtime і Rust tokenizer мають динамічний API; масиви нижче явно типізовано.
        ort: Any = import_module("onnxruntime")
        tokenizer_module: Any = import_module("tokenizers")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        self.session: Any = ort.InferenceSession(
            str(model_path / "model_quint8_avx2.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self.tokenizer: Any = tokenizer_module.Tokenizer.from_file(
            str(model_path / "tokenizer.json")
        )
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding()
        self.chunk_tokenizer: Any = tokenizer_module.Tokenizer.from_file(
            str(model_path / "tokenizer.json")
        )
        self.chunk_tokenizer.no_truncation()

    def chunks(self, text: str, size: int = 200, overlap: int = 40) -> list[str]:
        ids: list[int] = self.chunk_tokenizer.encode(text, add_special_tokens=False).ids
        return [
            str(self.chunk_tokenizer.decode(ids[start : start + size]))
            for start in range(0, len(ids), size - overlap)
        ] or [""]

    def encode(self, texts: Sequence[str]) -> Embedding:
        encodings: list[Any] = self.tokenizer.encode_batch(list(texts))
        feeds = {
            "input_ids": np.asarray([e.ids for e in encodings], dtype=np.int64),
            "attention_mask": np.asarray([e.attention_mask for e in encodings], dtype=np.int64),
            "token_type_ids": np.asarray([e.type_ids for e in encodings], dtype=np.int64),
        }
        embeddings = np.asarray(self.session.run(None, feeds)[0], dtype=np.float32)
        mask = feeds["attention_mask"].astype(np.float32)[:, :, None]
        pooled = (embeddings * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        return np.asarray(pooled / np.maximum(norms, 1e-9), dtype=np.float32)


def fingerprint(index: Index) -> str:
    digest = hashlib.sha256()
    for doc_id, meta in sorted(index.doc_meta.items()):
        digest.update(str(doc_id).encode())
        digest.update(meta.text.encode("utf-8"))
    return digest.hexdigest()


def embed(
    index: Index,
    model: MiniLM,
    out: Path,
    *,
    batch_size: int = 32,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    doc_ids: list[int] = []
    for doc_id, meta in sorted(index.doc_meta.items()):
        pieces = model.chunks(meta.text)
        chunks.extend(pieces)
        doc_ids.extend([doc_id] * len(pieces))
    batches: list[Embedding] = []
    for start in range(0, len(chunks), batch_size):
        batches.append(model.encode(chunks[start : start + batch_size]))
        if progress:
            progress(min(start + batch_size, len(chunks)), len(chunks))
    matrix = np.concatenate(batches) if batches else np.empty((0, 384), dtype=np.float32)
    np.save(out / "embeddings.npy", matrix, allow_pickle=False)
    np.save(out / "doc_ids.npy", np.asarray(doc_ids, dtype=np.int32), allow_pickle=False)
    metadata = {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "revision": MODEL_REVISION,
        "backend": "ONNX uint8 AVX2, attention-mask mean pooling, L2 normalization",
        "chunks": len(chunks),
        "dimensions": int(matrix.shape[1]),
        "documents": index.num_docs,
        "fingerprint": fingerprint(index),
        "chunk_tokens": 200,
        "overlap_tokens": 40,
    }
    (out / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return metadata


class SemanticIndex:
    def __init__(self, index: Index, path: Path, model: MiniLM) -> None:
        self.index = index
        self.model = model
        self.embeddings: Embedding = np.load(
            path / "embeddings.npy", mmap_mode="r", allow_pickle=False
        )
        self.doc_ids: NDArray[np.int32] = np.load(path / "doc_ids.npy", allow_pickle=False)
        self.chunks: list[str] = json.loads((path / "chunks.json").read_text(encoding="utf-8"))
        metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        if metadata["fingerprint"] != fingerprint(index):
            raise ValueError("Ембеддинги належать іншому корпусу; повторіть findex embed")
        self.ids = np.asarray(sorted(index.doc_meta), dtype=np.int32)

    def query_vector(self, query: str) -> Embedding:
        return np.asarray(self.model.encode([query])[0], dtype=np.float32)

    def search(self, query: str, k: int = 10) -> list[SearchResult]:
        query_vector = self.query_vector(query)
        cosine = np.asarray(self.embeddings @ query_vector, dtype=np.float64)
        rows = np.searchsorted(self.ids, self.doc_ids)
        best = np.full(len(self.ids), -np.inf, dtype=np.float64)
        np.maximum.at(best, rows, cosine)
        selected = top_k(self.ids, best, k)
        terms = tuple(tokenize(query))
        result: list[SearchResult] = []
        for row in selected:
            doc_id = int(self.ids[row])
            chunk_indices = np.flatnonzero(self.doc_ids == doc_id)
            chunk_id = int(chunk_indices[np.argmax(cosine[chunk_indices])])
            result.append(
                SearchResult(
                    doc_id,
                    float(best[row]),
                    self.index.doc_meta[doc_id].title,
                    snippet(self.chunks[chunk_id], terms),
                )
            )
        return result


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[SearchResult]], *, k: int = 10, rank_constant: int = 60
) -> list[SearchResult]:
    scores: dict[int, float] = {}
    originals: dict[int, SearchResult] = {}
    for ranking in rankings:
        for rank, result in enumerate(ranking, 1):
            scores[result.doc_id] = scores.get(result.doc_id, 0) + 1 / (rank_constant + rank)
            originals.setdefault(result.doc_id, result)
    best = sorted(scores, key=lambda i: (-scores[i], i))[:k]
    return [SearchResult(i, scores[i], originals[i].title, originals[i].snippet) for i in best]


@lru_cache(maxsize=2)
def get_semantic(index: Index, path: Path, model_path: Path) -> SemanticIndex:
    return SemanticIndex(index, path, MiniLM(model_path))
