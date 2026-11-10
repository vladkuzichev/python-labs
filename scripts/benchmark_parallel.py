"""Медіани ≥3 запусків; справжній peak RSS батьківського процесу семплується."""

import argparse
import json
import os
import platform
import statistics
import sys
import threading
from dataclasses import asdict
from pathlib import Path

from findex.parallel import build_parallel


def one(corpus, executor, workers):
    import psutil

    process = psutil.Process()
    samples = []
    stop = threading.Event()

    def sample():
        while not stop.wait(0.005):
            samples.append(process.memory_info().rss)

    monitor = threading.Thread(target=sample, daemon=True)
    monitor.start()
    try:
        index, metrics = build_parallel(corpus, executor=executor, workers=workers, positions=True)
    finally:
        samples.append(process.memory_info().rss)
        stop.set()
        monitor.join()
    return {**asdict(metrics), "parent_peak_rss": max(samples), "documents": index.num_docs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--free-threaded", action="store_true")
    args = parser.parse_args()
    corpus = Path("data/stdlib.jsonl")
    if args.free_threaded:
        # Вимір в окремому CPython 3.13t без C-розширень, які могли б увімкнути GIL.
        rows = []
        for workers in sorted({1, 2, 4, 8, os.cpu_count() or 1}):
            runs = []
            for _ in range(3):
                _, m = build_parallel(corpus, executor="threads", workers=workers, positions=True)
                runs.append(asdict(m))
            row = {
                "executor": "threads-free-threaded",
                "workers": workers,
                **{k: statistics.median(r[k] for r in runs) for k in runs[0]},
                "runs": runs,
                "gil_enabled": sys._is_gil_enabled(),
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
        Path("../Tests/lab05_free_threaded.json").write_text(json.dumps(rows, indent=2))
        return
    rows = []
    for executor in ["serial", "threads", "processes"]:
        for workers in sorted({1, 2, 4, 8, os.cpu_count() or 1}):
            runs = [one(corpus, executor, workers) for _ in range(3)]
            row = {
                "executor": executor,
                "workers": workers,
                "runs": runs,
                **{k: statistics.median(r[k] for r in runs) for k in runs[0]},
            }
            rows.append(row)
            Path("../Tests/lab05_parallel.json").write_text(json.dumps(rows, indent=2))
            print(executor, workers, round(row["wall_s"], 4), flush=True)
    Path("../Tests/machine.json").write_text(
        json.dumps(
            {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "logical_cpus": os.cpu_count(),
                "python": sys.version,
            },
            indent=2,
        )
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = rows[0]["wall_s"]
    for executor in ["serial", "threads", "processes"]:
        selected = [r for r in rows if r["executor"] == executor]
        plt.plot(
            [r["workers"] for r in selected],
            [base / r["wall_s"] for r in selected],
            "-o",
            label=executor,
        )
    maximum = max(r["workers"] for r in rows)
    plt.plot([1, maximum], [1, maximum], "--", label="Ideal linear")
    plt.xlabel("Workers")
    plt.ylabel("Speedup")
    plt.legend()
    plt.grid()
    Path("docs").mkdir(exist_ok=True)
    plt.savefig("docs/parallel_speedup.png", dpi=160, bbox_inches="tight")


if __name__ == "__main__":
    main()
