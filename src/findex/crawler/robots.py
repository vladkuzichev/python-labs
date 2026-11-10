from __future__ import annotations

import asyncio
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from findex.crawler.fetch import fetch

USER_AGENT = "findex-lab/1.0 (+http://127.0.0.1:8000/; local educational crawler)"


class RobotsCache:
    def __init__(self, client: httpx.AsyncClient, user_agent: str = USER_AGENT) -> None:
        self.client = client
        self.user_agent = user_agent
        self.cache: dict[str, RobotFileParser] = {}
        self.locks: dict[str, asyncio.Lock] = {}

    async def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        lock = self.locks.setdefault(origin, asyncio.Lock())
        async with lock:
            if origin not in self.cache:
                result = await fetch(self.client, origin + "/robots.txt")
                parser = RobotFileParser(origin + "/robots.txt")
                if result.status == 200:
                    parser.parse(result.content.decode("utf-8", errors="replace").splitlines())
                elif result.status == 404:
                    parser.parse(["User-agent: *", "Allow: /"])
                else:
                    parser.parse(["User-agent: *", "Disallow: /"])
                self.cache[origin] = parser
        return self.cache[origin].can_fetch(self.user_agent, url)
