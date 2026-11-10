"""Статистика за один прохід та навмисно жадібна контрольна реалізація."""

import argparse
import json
import time
import tracemalloc
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import islice
from pathlib import Path

from findex.corpus import iter_documents
from findex.tokenize import tokenize


@dataclass(frozen=True, slots=True)
class CorpusStats:
    documents: int
    tokens: int
    vocabulary: int
    top50: list[tuple[str, int]]


def collect(root: Path, limit: int | None = None, *, eager: bool = False) -> CorpusStats:
    docs = islice(iter_documents(root), limit)
    counts: Counter[str] = Counter()
    num_docs = 0
    if eager:
        materialized = list(docs)
        token_lists = [list(tokenize(doc.text)) for doc in materialized]
        for tokens in token_lists:
            counts.update(tokens)
        num_docs = len(materialized)
    else:
        for doc in docs:
            counts.update(tokenize(doc.text))
            num_docs += 1
    return CorpusStats(num_docs, counts.total(), len(counts), counts.most_common(50))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--eager", action="store_true")
    args = parser.parse_args()
    tracemalloc.start()
    started = time.perf_counter()
    result = collect(args.corpus, args.limit, eager=args.eager)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(
        json.dumps({**asdict(result), "elapsed_s": elapsed, "peak_bytes": peak}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
