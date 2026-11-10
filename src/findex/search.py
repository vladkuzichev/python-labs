"""Boolean-пошук зі збереженого індексу (розширюється ранжуванням у ЛР 3)."""

from __future__ import annotations

import argparse
import time
import tracemalloc
from pathlib import Path

from findex.boolean import Engine, combine
from findex.index import Index
from findex.tokenize import tokenize


def boolean_search(index: Index, query: str, *, engine: Engine = "merge") -> list[int]:
    result: list[int] | None = None
    operation = "AND"
    for part in query.split():
        if part in {"AND", "OR", "NOT"}:
            operation = part
            continue
        terms = list(tokenize(part))
        if not terms:
            raise ValueError("Порожній термін")
        values = [p.doc_id for p in index.postings.get(terms[0], [])]
        if result is None:
            result = combine(sorted(index.doc_meta), values, "NOT", engine) if operation == "NOT" else values
        else:
            result = combine(result, values, operation, engine)
        operation = "AND"
    return result or []


def main() -> None:
    from findex.store import load

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("query")
    parser.add_argument("--engine", choices=["merge", "set"], default="merge")
    args = parser.parse_args()
    tracemalloc.start()
    started = time.perf_counter()
    index = load(args.index)
    results = boolean_search(index, args.query, engine=args.engine)
    for doc_id in results[:10]:
        print(doc_id, index.doc_meta[doc_id].title)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"matches={len(results)} elapsed_s={time.perf_counter()-started:.6f} peak_bytes={peak}")


if __name__ == "__main__":
    main()
