"""Boolean-пошук зі збереженого індексу (розширюється ранжуванням у ЛР 3)."""

from __future__ import annotations

import argparse
import html
import logging
import re
import time
import tracemalloc
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from heapq import nlargest
from pathlib import Path

from findex.boolean import Engine
from findex.index import Index
from findex.instrument import timed
from findex.query import parse
from findex.scoring import BM25, Scorer

logger = logging.getLogger(__name__)


@dataclass(order=True, frozen=True, slots=True)
class SearchResult:
    sort_key: tuple[float, int] = field(init=False, repr=False)
    doc_id: int = field(compare=False)
    score: float = field(compare=False)
    title: str = field(compare=False)
    snippet: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "sort_key", (self.score, -self.doc_id))


@lru_cache(maxsize=256)
def candidate_ids(index: Index, query: str, engine: Engine = "merge") -> tuple[int, ...]:
    if index.closed:
        raise ValueError("Індекс закрито")
    return tuple(parse(query).evaluate(index, engine))


def snippet(text: str, terms: tuple[str, ...], radius: int = 80) -> str:
    if not terms:
        return html.escape(text[: radius * 2])
    pattern = re.compile(
        r"(?<!\w)(?:" + "|".join(re.escape(t) for t in set(terms)) + r")(?!\w)", re.I
    )
    matches = list(pattern.finditer(text))
    best = max(
        matches,
        key=lambda m: len(
            set(pattern.findall(text[max(0, m.start() - radius) : m.end() + radius]))
        ),
        default=None,
    )
    start = max(0, best.start() - radius) if best else 0
    end = min(len(text), best.end() + radius) if best else min(len(text), radius * 2)
    window = text[start:end]
    pieces: list[str] = []
    previous = 0
    for match in pattern.finditer(window):
        pieces.extend(
            (
                html.escape(window[previous : match.start()]),
                "<mark>",
                html.escape(match.group()),
                "</mark>",
            )
        )
        previous = match.end()
    pieces.append(html.escape(window[previous:]))
    return ("…" if start else "") + "".join(pieces) + ("…" if end < len(text) else "")


@timed
def search(
    index: Index,
    query: str,
    *,
    scorer: Scorer | None = None,
    k: int = 10,
    engine: Engine = "merge",
    with_snippets: bool = True,
) -> list[SearchResult]:
    if k < 1:
        raise ValueError("k має бути додатним")
    scorer = scorer or BM25()
    before = candidate_ids.cache_info()
    allowed = set(candidate_ids(index, query, engine))
    after = candidate_ids.cache_info()
    logger.info(
        "query_cache hit=%s hits=%d misses=%d", after.hits > before.hits, after.hits, after.misses
    )
    terms = tuple(dict.fromkeys(parse(query).terms()))
    scores: defaultdict[int, float] = defaultdict(float)
    for term in terms:
        for posting in index.postings.get(term, []):
            if posting.doc_id in allowed:
                scores[posting.doc_id] += scorer.score(term, posting, index)
    for doc_id in allowed:
        scores.setdefault(doc_id, 0.0)
    best = nlargest(k, scores, key=lambda doc_id: (scores[doc_id], -doc_id))
    return [
        SearchResult(
            i,
            scores[i],
            index.doc_meta[i].title,
            snippet(index.doc_meta[i].text, terms) if with_snippets else "",
        )
        for i in best
    ]


def boolean_search(index: Index, query: str, *, engine: Engine = "merge") -> list[int]:
    return list(candidate_ids(index, query, engine))


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
    print(f"matches={len(results)} elapsed_s={time.perf_counter() - started:.6f} peak_bytes={peak}")


if __name__ == "__main__":
    main()
