from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FetchResult:
    url: str
    status: int
    content: bytes
    elapsed_s: float
    attempts: int
    headers: dict[str, str]
    error: str | None = None


def retry_delay(value: str | None, attempt: int) -> float:
    if value is not None:
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                return max(0.0, (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return float(0.1 * 2**attempt + random.uniform(0, 0.05))


async def fetch(
    client: httpx.AsyncClient, url: str, *, timeout: float = 10.0, max_retries: int = 3
) -> FetchResult:
    started = time.perf_counter()
    for attempt in range(max_retries + 1):
        try:
            async with asyncio.timeout(timeout):
                response = await client.get(url, timeout=timeout, follow_redirects=False)
            elapsed = time.perf_counter() - started
            logger.info(
                "url=%s status=%d bytes=%d elapsed_s=%.5f attempt=%d",
                url,
                response.status_code,
                len(response.content),
                elapsed,
                attempt + 1,
            )
            if (
                response.status_code == 429 or response.status_code >= 500
            ) and attempt < max_retries:
                delay = retry_delay(response.headers.get("Retry-After"), attempt)
                logger.warning(
                    "retry url=%s status=%d delay_s=%.3f", url, response.status_code, delay
                )
                await asyncio.sleep(delay)
                continue
            return FetchResult(
                url,
                response.status_code,
                response.content,
                elapsed,
                attempt + 1,
                dict(response.headers),
            )
        except (TimeoutError, httpx.TimeoutException, httpx.NetworkError) as error:
            logger.warning(
                "url=%s status=0 attempt=%d error=%s", url, attempt + 1, type(error).__name__
            )
            if attempt == max_retries:
                return FetchResult(
                    url, 0, b"", time.perf_counter() - started, attempt + 1, {}, str(error)
                )
            await asyncio.sleep(retry_delay(None, attempt))
    raise AssertionError("unreachable")
