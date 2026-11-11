import asyncio
import threading

import httpx
import pytest

from findex.crawler.crawl import canonicalize, crawl
from findex.crawler.fetch import fetch, retry_delay
from findex.crawler.robots import RobotsCache


def test_canonical():
    assert (
        canonicalize("HTTP://Example.COM:80/a/../b/?z=2&a=1#frag") == "http://example.com/b?a=1&z=2"
    )


@pytest.mark.parametrize("url", ["file:///etc/passwd", "https://user:pass@a/", "mailto:a@b"])
def test_bad_url(url):
    with pytest.raises(ValueError):
        canonicalize(url)


def test_retries(caplog):
    attempts = []

    def handler(request):
        attempts.append(request.url)
        return httpx.Response(
            429 if len(attempts) < 2 else 200, headers={"Retry-After": "0"}, text="ok"
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch(client, "http://local/")

    result = asyncio.run(run())
    assert result.status == 200 and result.attempts == 2
    assert "status=429" in caplog.text


def test_no_retry_404():
    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: httpx.Response(404))
        ) as client:
            return await fetch(client, "http://local/")

    assert asyncio.run(run()).attempts == 1


def test_timeout():
    async def handler(request):
        await asyncio.sleep(0.05)
        return httpx.Response(200)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch(client, "http://local/", timeout=0.001, max_retries=0)

    assert asyncio.run(run()).status == 0


def test_robots_cached():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, text="User-agent: *\nDisallow: /private\n")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            cache = RobotsCache(client)
            assert not await cache.allowed("http://local/private")
            assert await cache.allowed("http://local/public")

    asyncio.run(run())
    assert len(calls) == 1


def test_crawl_limits_and_redirect():
    requests = []

    def handler(request):
        url = str(request.url)
        requests.append(url)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /secret")
        if request.url.path == "/redirect":
            return httpx.Response(302, headers={"Location": "http://forbidden/private"})
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text="""<title>Page</title>
            <a href="/one/">one</a><a href="/one#frag">same</a><a href="/secret">secret</a>
            <a href="/two">two</a><a href="/redirect">redir</a><script>hidden</script>""",
        )

    async def run():
        return [
            p
            async for p in crawl(
                ["http://local/"],
                max_pages=20,
                concurrency=5,
                per_host=2,
                min_delay=0,
                transport=httpx.MockTransport(handler),
            )
        ]

    pages = asyncio.run(run(), debug=True)
    assert len(pages) == 3
    assert len(set(requests)) == len(requests)
    assert not any("forbidden" in u or "/secret" in u for u in requests)
    assert all("hidden" not in p.text for p in pages)


def test_max_pages_and_early_close():
    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(
            200, headers={"content-type": "text/html"}, text='<a href="/a">a</a><a href="/b">b</a>'
        )

    async def run():
        generator = crawl(
            ["http://local/"],
            max_pages=1,
            concurrency=3,
            min_delay=0,
            transport=httpx.MockTransport(handler),
        )
        pages = [p async for p in generator]
        assert len(pages) == 1
        generator = crawl(
            ["http://local/"], max_pages=10, min_delay=0, transport=httpx.MockTransport(handler)
        )
        await anext(generator)
        await generator.aclose()

    asyncio.run(run(), debug=True)


def test_retry_after():
    assert retry_delay("2", 0) == 2
    assert 0 <= retry_delay("Mon, 01 Jan 2001 00:00:00 GMT", 0) <= 0.1
    assert retry_delay("bad", 0) >= 0.1


def test_client_initialization_does_not_block_event_loop(monkeypatch):
    original = httpx.AsyncClient
    started = threading.Event()
    release = threading.Event()
    completed = threading.Event()

    def delayed_client(**kwargs):
        started.set()
        release.wait(2)
        completed.set()
        return original(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", delayed_client)

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(
            200, headers={"content-type": "text/html"}, text="<title>Ready</title>page"
        )

    async def run():
        generator = crawl(
            ["http://local/"], max_pages=1, min_delay=0, transport=httpx.MockTransport(handler)
        )
        pending = asyncio.create_task(anext(generator))
        try:
            assert await asyncio.to_thread(started.wait, 1)
            # The loop must make progress while synchronous initialization is
            # deliberately held open. The old code waits two seconds here.
            await asyncio.sleep(0)
            assert not completed.is_set()
        finally:
            release.set()
        page = await asyncio.wait_for(pending, 3)
        assert page.title == "Ready"
        await generator.aclose()

    asyncio.run(run(), debug=True)
