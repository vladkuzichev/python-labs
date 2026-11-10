import asyncio
import json
import logging
import time
from dataclasses import asdict
from pathlib import Path

import httpx
import psutil

from findex.crawler.crawl import CrawlStats, crawl


async def main():
    rows = []
    logging.basicConfig(
        filename="../Tests/lab06_crawl.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        encoding="utf-8",
    )
    for concurrency in [1, 5, 20]:
        async with httpx.AsyncClient() as client:
            (await client.post("http://127.0.0.1:8766/reset")).raise_for_status()
        state = CrawlStats()
        rss = []
        started = time.perf_counter()
        with Path(f"data/crawl_{concurrency}.jsonl").open("w", encoding="utf-8") as stream:
            async for page in crawl(
                ["http://127.0.0.1:8766/"],
                max_pages=200,
                concurrency=concurrency,
                per_host=20,
                min_delay=0.002,
                stats=state,
            ):
                stream.write(json.dumps(asdict(page), ensure_ascii=False) + "\n")
                stream.flush()
                rss.append(psutil.Process().memory_info().rss)
        wall = time.perf_counter() - started
        row = {
            "concurrency": concurrency,
            "pages": state.pages,
            "wall_s": wall,
            "pages_per_second": state.pages / wall,
            "errors": state.errors,
            "peak_rss": max(rss),
            "model_latency_s": 0.015,
            "min_delay_s": 0.002,
            "per_host": 20,
        }
        rows.append(row)
        print(json.dumps(row), flush=True)
    Path("../Tests/lab06_benchmark.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
