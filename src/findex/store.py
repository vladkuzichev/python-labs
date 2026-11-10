"""Два формати зберігання. Pickle можна читати лише зі свого довіреного файлу."""

from __future__ import annotations

import json
import pickle
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

from findex.index import DocMeta, Index, Posting
from findex.instrument import timed

Format = Literal["json", "pickle"]


def to_dict(index: Index) -> dict[str, Any]:
    return {
        "schema": 1,
        "positions": index.positions,
        "postings": {
            term: [asdict(p) for p in values] for term, values in sorted(index.postings.items())
        },
        "doc_lengths": index.doc_lengths,
        "doc_meta": {str(doc_id): asdict(meta) for doc_id, meta in index.doc_meta.items()},
    }


def from_dict(data: dict[str, Any]) -> Index:
    if data.get("schema") != 1:
        raise ValueError("Непідтримувана версія індексу")
    index = Index(
        {
            str(term): [
                Posting(int(p["doc_id"]), int(p["tf"]), tuple(p["positions"])) for p in values
            ]
            for term, values in data["postings"].items()
        },
        {int(i): int(n) for i, n in data["doc_lengths"].items()},
        {int(i): DocMeta(**meta) for i, meta in data["doc_meta"].items()},
        bool(data["positions"]),
    )
    for values in index.postings.values():
        ids = [p.doc_id for p in values]
        if ids != sorted(set(ids)) or any(
            p.tf <= 0 or p.doc_id not in index.doc_meta for p in values
        ):
            raise ValueError("Пошкоджені постінги")
    return index


def save(index: Index, path: Path, *, format: Format | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kind = format or ("json" if path.suffix == ".json" else "pickle")
    if kind == "json":
        path.write_text(json.dumps(to_dict(index), ensure_ascii=False), encoding="utf-8")
    else:
        with path.open("wb") as stream:
            pickle.dump(to_dict(index), stream, protocol=5)


@timed
def load(path: Path, *, format: Format | None = None) -> Index:
    kind = format or ("json" if path.suffix == ".json" else "pickle")
    if kind == "json":
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
    else:
        # pickle.load виконує інструкції pickle; чужий файл здатний виконати довільний код.
        # Цей шлях призначений виключно для локальних індексів, побудованих користувачем.
        with path.open("rb") as stream:
            data = pickle.load(stream)
    return from_dict(data)


@contextmanager
def open_index(path: Path) -> Iterator[Index]:
    index = load(path)
    try:
        yield index
    finally:
        index.close()
