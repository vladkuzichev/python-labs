"""Справжні localhost HTTP-запити, oha і окремий дослід 20 одночасних запитів."""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import certifi
import httpx
import psutil


async def concurrent_20(url):
    async with httpx.AsyncClient() as client:
        started = time.perf_counter()
        responses = await asyncio.gather(*(client.get(url, timeout=30) for _ in range(20)))
        assert all(r.status_code == 200 for r in responses)
        return time.perf_counter() - started


def main():
    root = Path("../Tests")
    servers = []
    handles = []
    env = {
        **os.environ,
        "INDEX_PATH": str(Path("data/index.bin").resolve()),
        "BACKEND": "python",
        "SSL_CERT_FILE": certifi.where(),
        "PYTHONUTF8": "1",
    }
    oha_candidates=[Path('../Offline/oha.exe'),Path('../../_work/oha.exe')]
    oha=next((p.resolve() for p in oha_candidates if p.exists()),None)
    if oha is None:
        raise FileNotFoundError('Не знайдено Offline/oha.exe')
    try:
        for port, style, workers in [(8001, "async", 1), (8002, "sync", 4)]:
            handle = (root / f"lab07_server_{port}.log").open("w", encoding="utf-8")
            handles.append(handle)
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "findex",
                    "serve",
                    "--port",
                    str(port),
                    "--workers",
                    str(workers),
                ],
                env={**env, "ROUTE_STYLE": style},
                stdout=handle,
                stderr=handle,
            )
            servers.append(child)
            for _ in range(100):
                try:
                    if httpx.get(f"http://127.0.0.1:{port}/health", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.1)
            else:
                raise RuntimeError(f"Сервер {port} не запустився")
        rows = []
        for label, port in [
            ("local-sync-1", 8000),
            ("local-async-1", 8001),
            ("local-sync-4", 8002),
        ]:
            url = f"http://127.0.0.1:{port}/search?q=the%20file%20return"
            json_path = root / f"lab07_oha_{label}.json"
            run = subprocess.run(
                [
                    str(oha),
                    "--output-format",
                    "json",
                    "--no-tui",
                    "-n",
                    "1000",
                    "-c",
                    "50",
                    url,
                    "-o",
                    str(json_path),
                ],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if run.returncode:
                (root / f"lab07_oha_{label}.error.txt").write_text(run.stderr, encoding="utf-8")
                raise RuntimeError("oha: " + run.stderr[:300])
            data = json.loads(json_path.read_text())
            assert data["summary"]["successRate"] == 1
            latency = data["metrics"]["latency_ms"]
            rows.append(
                {
                    "target": label,
                    "tool": "oha 1.16.0",
                    "requests": 1000,
                    "concurrency": 50,
                    "rps": data["summary"]["requestsPerSec"],
                    **{k: latency[k] for k in ["p50", "p95", "p99"]},
                    "twenty_concurrent_s": asyncio.run(concurrent_20(url)),
                }
            )
            (root / "lab07_load.json").write_text(json.dumps(rows, indent=2))
            print(json.dumps(rows[-1]), flush=True)
    finally:
        for child in servers:
            try:
                descendants = psutil.Process(child.pid).children(recursive=True)
            except psutil.NoSuchProcess:
                descendants = []
            child.terminate()
            for descendant in descendants:
                try:
                    descendant.terminate()
                except psutil.NoSuchProcess:
                    pass
            child.wait(timeout=10)
        for handle in handles:
            handle.close()


if __name__ == "__main__":
    main()
