"""Ті самі незалежні часткові індекси для циклу, потоків і spawn-процесів."""

from __future__ import annotations

import heapq
import json
import logging
import multiprocessing
import tempfile
import time
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Literal

from findex.corpus import Document, iter_documents
from findex.index import DocMeta, Index, Posting, build_index

Executor = Literal["serial", "threads", "processes"]
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Work:
    paths: list[Path]
    start_id: int
    positions: bool


@dataclass
class PartialIndex:
    index: Index
    cpu_s: float


def build_partial(work: Work) -> PartialIndex:
    """Аргументи — шляхи й початковий ID; функція придатна до pickle/spawn."""
    started = time.thread_time()

    def documents() -> Iterator[Document]:
        next_id = work.start_id
        for path in work.paths:
            for doc in iter_documents(path):
                yield Document(next_id, doc.path, doc.text, doc.title)
                next_id += 1

    index = build_index(documents(), positions=work.positions)
    return PartialIndex(index, time.thread_time() - started)


def merge(partials: Iterable[PartialIndex]) -> Index:
    groups: defaultdict[str, list[Sequence[Posting]]] = defaultdict(list)
    lengths: dict[int, int] = {}
    metadata: dict[int, DocMeta] = {}
    positions = False
    for partial in partials:
        index = partial.index
        if lengths.keys() & index.doc_lengths.keys():
            raise ValueError("Діапазони doc_id часткових індексів перетинаються")
        lengths.update(index.doc_lengths)
        metadata.update(index.doc_meta)
        positions = index.positions
        for term, posting_list in index.postings.items():
            groups[term].append(posting_list)
    merged_postings = {
        term: list(heapq.merge(*lists, key=lambda p: p.doc_id)) for term, lists in groups.items()
    }
    return Index(
        dict(sorted(merged_postings.items())),
        dict(sorted(lengths.items())),
        dict(sorted(metadata.items())),
        positions,
    )


@contextmanager
def chunks(corpus: Path, workers: int, positions: bool, limit: int | None) -> Iterator[list[Work]]:
    if corpus.is_dir():
        paths = list(islice(corpus.rglob("*.txt"), limit))
        size = max(1, (len(paths) + workers - 1) // workers)
        yield [Work(paths[i : i + size], i, positions) for i in range(0, len(paths), size)]
        return
    if corpus.suffix != ".jsonl":
        yield [Work([corpus], 0, positions)]
        return
    # JSONL розбивається потоково на файли: воркерам не передаються тексти через pickle.
    # Копіювання входить у wall time і є окремим послідовним обмеженням.
    count = sum(1 for _ in islice(iter_documents(corpus), limit))
    size = max(1, (count + workers - 1) // workers)
    with tempfile.TemporaryDirectory(prefix="findex-", dir=corpus.parent) as temporary:
        work: list[Work] = []
        source = islice(iter_documents(corpus), limit)
        for start in range(0, count, size):
            path = Path(temporary) / f"chunk-{start}.jsonl"
            with path.open("w", encoding="utf-8") as stream:
                for doc in islice(source, size):
                    stream.write(
                        json.dumps(
                            {"path": doc.path, "title": doc.title, "text": doc.text},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            work.append(Work([path], start, positions))
        yield work


@dataclass(frozen=True, slots=True)
class BuildMetrics:
    wall_s: float
    cpu_s: float
    merge_s: float


def build_parallel(
    corpus: Path,
    *,
    workers: int = 1,
    executor: Executor = "serial",
    positions: bool = False,
    limit: int | None = None,
) -> tuple[Index, BuildMetrics]:
    if workers < 1 or executor not in {"serial", "threads", "processes"}:
        raise ValueError("workers ≥ 1; executor: serial, threads, processes")
    started, cpu_started = time.perf_counter(), time.process_time()
    with chunks(corpus, workers, positions, limit) as work:
        if executor == "serial":
            partials = [build_partial(item) for item in work]
        elif executor == "threads":
            with ThreadPoolExecutor(max_workers=workers) as pool:
                try:
                    partials = list(pool.map(build_partial, work))
                except Exception:
                    logger.exception("Помилка потокового воркера; побудову зупинено")
                    raise
        else:
            with ProcessPoolExecutor(
                max_workers=workers, mp_context=multiprocessing.get_context("spawn")
            ) as pool:
                try:
                    partials = list(pool.map(build_partial, work))
                except Exception:
                    logger.exception("Помилка процесного воркера; побудову зупинено")
                    raise
        merge_started = time.perf_counter()
        index = merge(partials)
        merge_s = time.perf_counter() - merge_started
    cpu_s = time.process_time() - cpu_started
    if executor == "processes":
        cpu_s += sum(p.cpu_s for p in partials)
    return index, BuildMetrics(time.perf_counter() - started, cpu_s, merge_s)
