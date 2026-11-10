"""Єдина точка входу: дані — stdout, діагностика — stderr."""

from __future__ import annotations

import html
import json
import logging
import re
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterator
from enum import Enum
from functools import wraps
from itertools import islice
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import track
from rich.table import Table
from rich.text import Text

from findex.corpus import Document, iter_documents
from findex.index import build_index
from findex.parallel import build_parallel
from findex.scoring import BM25, TfIdf
from findex.search import search as run_search
from findex.store import load, save

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    help="findex — пошук у документації Python",
)
console = Console()
diagnostics = Console(stderr=True)


class EngineOption(str, Enum):
    merge = "merge"
    set = "set"


class ExecutorOption(str, Enum):
    serial="serial"
    threads="threads"
    processes="processes"


def expected_errors[**P, T](function: Callable[P, T]) -> Callable[P, T]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return function(*args, **kwargs)
        except (OSError, ValueError, KeyError, EOFError) as error:
            diagnostics.print(f"Помилка: {error}", markup=False)
            raise typer.Exit(code=2) from None

    return wrapper


@app.callback()
def configure(verbose: Annotated[int, typer.Option("--verbose", "-v", count=True)] = 0) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose > 1 else logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )


@app.command("index")
@expected_errors
def index_command(
    corpus: Path,
    out: Annotated[Path, typer.Option("--out")] = Path("data/index.bin"),
    positions: bool = False,
    limit: Annotated[int | None, typer.Option(min=0)] = None,
    workers: Annotated[int, typer.Option(min=1)] = 1,
    executor: ExecutorOption = ExecutorOption.serial,
) -> None:
    def documents() -> Iterator[Document]:
        yield from track(
            islice(iter_documents(corpus), limit),
            description="Індексація",
            console=diagnostics,
            disable=not diagnostics.is_terminal,
        )

    started = time.perf_counter()
    if executor == ExecutorOption.serial and workers == 1:
        index = build_index(documents(), positions=positions)
    else:
        index, metrics = build_parallel(corpus, workers=workers, executor=executor.value, positions=positions, limit=limit)
        logging.getLogger(__name__).info("build metrics=%s", metrics)
    save(index, out)
    console.print(
        f"Документів: {index.num_docs}; термінів: {len(index)}; "
        f"час: {time.perf_counter() - started:.4f} с; індекс: {out}"
    )


@app.command("search")
@expected_errors
def search_command(
    index_path: Path,
    query: str,
    k: Annotated[int, typer.Option(min=1, max=1000)] = 10,
    scorer: Annotated[str, typer.Option()] = "bm25",
    engine: EngineOption = EngineOption.merge,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    if scorer not in {"bm25", "tfidf"}:
        raise ValueError("scorer: bm25 або tfidf")
    index = load(index_path)
    results = run_search(
        index,
        query,
        scorer=BM25() if scorer == "bm25" else TfIdf(),
        k=k,
        engine=engine.value,
    )
    if json_output:
        for result in results:
            typer.echo(
                json.dumps(
                    {
                        "doc_id": result.doc_id,
                        "score": result.score,
                        "title": result.title,
                        "snippet": result.snippet,
                    },
                    ensure_ascii=False,
                )
            )
        return
    table = Table(title=f"Результати: {query}")
    for name in ["ID", "Бали", "Документ / фрагмент"]:
        table.add_column(name)
    for result in results:
        text = Text(result.title + "\n", style="bold cyan")
        clean = html.unescape(re.sub(r"</?mark>", "", result.snippet))
        text.append(clean, style="none")
        for term in parse_terms(query):
            text.highlight_regex(re.compile(re.escape(term), re.I), style="bold yellow")
        table.add_row(str(result.doc_id), f"{result.score:.5f}", text)
    console.print(table)


def parse_terms(query: str) -> tuple[str, ...]:
    from findex.query import parse

    return parse(query).terms()


@app.command("stats")
@expected_errors
def stats_command(index_path: Path) -> None:
    index = load(index_path)
    counts = Counter({term: sum(p.tf for p in values) for term, values in index.postings.items()})
    console.print_json(
        data={
            "documents": index.num_docs,
            "tokens": sum(index.doc_lengths.values()),
            "vocabulary": len(index),
            "top50": counts.most_common(50),
            "avg_doc_length": index.avg_doc_length,
        }
    )


if __name__ == "__main__":
    app()
