from __future__ import annotations

import asyncio
import logging
import posixpath
import time
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx

from findex.crawler.fetch import fetch
from findex.crawler.robots import USER_AGENT, RobotsCache

logger = logging.getLogger(__name__)


def canonicalize(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username:
        raise ValueError("Потрібна HTTP(S) адреса без облікових даних")
    scheme = parts.scheme.lower()
    host = parts.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    port = parts.port
    if port and not (scheme == "http" and port == 80 or scheme == "https" and port == 443):
        host += f":{port}"
    path = posixpath.normpath(parts.path or "/")
    if not path.startswith("/"):
        path = "/" + path
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return urlunsplit((scheme, host, path, query, ""))


class Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.text: list[str] = []
        self.title: list[str] = []
        self.skipped = 0
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.skipped += 1
        if tag == "title":
            self.in_title = True
        if tag == "a":
            for key, value in attrs:
                if key == "href" and value:
                    self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skipped = max(0, self.skipped - 1)
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if not self.skipped:
            self.text.append(data)
            if self.in_title:
                self.title.append(data)


@dataclass(frozen=True, slots=True)
class Page:
    url: str
    title: str
    text: str
    fetched_at: str


@dataclass
class CrawlStats:
    pages: int = 0
    errors: int = 0
    in_flight: int = 0
    queue_depth: int = 0
    started: float = field(default_factory=time.perf_counter)

    @property
    def pages_per_second(self) -> float:
        return self.pages / max(time.perf_counter() - self.started, 1e-9)


async def crawl(
    seeds: Iterable[str],
    *,
    max_pages: int = 500,
    concurrency: int = 10,
    per_host: int = 2,
    allowed_domains: set[str] | None = None,
    min_delay: float = 0.05,
    stats: CrawlStats | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
    user_agent: str = USER_AGENT,
) -> AsyncIterator[Page]:
    if max_pages < 1 or concurrency < 1 or per_host < 1 or min_delay < 0:
        raise ValueError("Некоректні ліміти обходу")
    seed_urls = [canonicalize(s) for s in seeds]
    domains = allowed_domains or {urlsplit(s).hostname or "" for s in seed_urls}
    state = stats if stats is not None else CrawlStats()
    frontier: asyncio.Queue[str] = asyncio.Queue()
    output: asyncio.Queue[Page | None] = asyncio.Queue(maxsize=concurrency * 2)
    seen: set[str] = set()
    global_limit = asyncio.Semaphore(concurrency)
    host_limits: dict[str, asyncio.Semaphore] = {}
    host_locks: dict[str, asyncio.Lock] = {}
    last_request: dict[str, float] = {}

    def enqueue(url: str) -> None:
        try:
            canonical = canonicalize(url)
        except ValueError:
            return
        if urlsplit(canonical).hostname in domains and canonical not in seen:
            seen.add(canonical)
            frontier.put_nowait(canonical)
            state.queue_depth = frontier.qsize()

    for seed in seed_urls:
        enqueue(seed)
    # SSL-context initialization can read certificate files synchronously. Keep
    # it off the event loop; the client itself is used by the loop afterwards.
    prepared_client = await asyncio.to_thread(
        httpx.AsyncClient, transport=transport, headers={"User-Agent": user_agent}
    )
    async with prepared_client as client:
        robots = RobotsCache(client, user_agent)

        async def worker() -> None:
            while True:
                url = await frontier.get()
                try:
                    if state.pages >= max_pages:
                        continue
                    host = urlsplit(url).netloc
                    semaphore = host_limits.setdefault(host, asyncio.Semaphore(per_host))
                    async with global_limit, semaphore:
                        if not await robots.allowed(url):
                            logger.info("robots_denied url=%s", url)
                            continue
                        lock = host_locks.setdefault(host, asyncio.Lock())
                        async with lock:
                            await asyncio.sleep(
                                max(
                                    0.0, last_request.get(host, 0) + min_delay - time.perf_counter()
                                )
                            )
                            last_request[host] = time.perf_counter()
                        state.in_flight += 1
                        try:
                            result = await fetch(client, url)
                        finally:
                            state.in_flight -= 1
                    if 300 <= result.status < 400 and "location" in result.headers:
                        enqueue(urljoin(url, result.headers["location"]))
                        continue
                    if result.status != 200:
                        state.errors += 1
                        continue
                    if "html" not in result.headers.get("content-type", "text/html"):
                        continue
                    parser = Extractor()
                    parser.feed(result.content.decode("utf-8", errors="replace"))
                    if state.pages >= max_pages:
                        continue
                    state.pages += 1
                    page = Page(
                        url,
                        "".join(parser.title).strip() or url,
                        " ".join(" ".join(parser.text).split()),
                        datetime.now(UTC).isoformat(),
                    )
                    await output.put(page)
                    if state.pages < max_pages:
                        for link in parser.links:
                            enqueue(urljoin(url, link))
                finally:
                    frontier.task_done()
                    state.queue_depth = frontier.qsize()

        async def finished() -> None:
            await frontier.join()
            await output.put(None)

        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(worker()) for _ in range(concurrency)]
            tasks.append(group.create_task(finished()))
            try:
                yielded = 0
                while yielded < max_pages:
                    page = await output.get()
                    if page is None:
                        break
                    yielded += 1
                    yield page
            except GeneratorExit:
                return
            finally:
                for task in tasks:
                    task.cancel()
                while not frontier.empty():
                    frontier.get_nowait()
                    frontier.task_done()
