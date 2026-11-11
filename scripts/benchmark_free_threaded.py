"""Зовнішній спостерігач RSS не імпортує GIL-залежні розширення у Python 3.13t."""

import json
import os
import statistics
import subprocess
import time
from pathlib import Path

import psutil


def main():
    candidates = [
        Path("../RuntimeFreeThreaded/python/python.exe"),
        Path("../../_work/runtime-t/python/python.exe"),
    ]
    interpreter = next((p.resolve() for p in candidates if p.exists()), None)
    if interpreter is None:
        raise FileNotFoundError("Потрібен RuntimeFreeThreaded/python/python.exe")
    env = {**os.environ, "PYTHONPATH": str(Path("src").resolve()), "PYTHONUTF8": "1"}
    rows = []
    for workers in sorted({1, 2, 4, 8, os.cpu_count() or 1}):
        runs = []
        for _ in range(3):
            code = (
                "import sys,json;from pathlib import Path;from dataclasses import asdict;"
                "from findex.parallel import build_parallel;"
                f'ix,m=build_parallel(Path("data/stdlib.jsonl"),workers={workers},'
                'executor="threads",positions=True);'
                'print(json.dumps({**asdict(m),"gil_enabled":sys._is_gil_enabled(),"documents":ix.num_docs}))'
            )
            child = subprocess.Popen(
                [str(interpreter), "-c", code],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process = psutil.Process(child.pid)
            peak = 0
            while child.poll() is None:
                try:
                    peak = max(peak, process.memory_info().rss)
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.005)
            stdout, stderr = child.communicate()
            if child.returncode:
                raise RuntimeError(stderr.decode("utf-8", errors="replace"))
            run = json.loads(stdout)
            run["parent_peak_rss"] = peak
            assert run["gil_enabled"] is False
            runs.append(run)
        row = {
            "executor": "threads-free-threaded",
            "workers": workers,
            "runs": runs,
            **{
                k: statistics.median(r[k] for r in runs)
                for k in ["wall_s", "cpu_s", "merge_s", "parent_peak_rss"]
            },
            "gil_enabled": False,
        }
        rows.append(row)
        print(workers, row["wall_s"], row["parent_peak_rss"], flush=True)
    Path("../Tests/lab05_free_threaded.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
