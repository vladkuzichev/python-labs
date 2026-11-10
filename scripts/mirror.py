"""Локальне дзеркало справжнього корпусу. Затримка 15 мс — явна модель I/O."""

import asyncio
import html
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

app = FastAPI()
docs = [
    json.loads(line) for line in Path("data/stdlib.jsonl").read_text(encoding="utf-8").splitlines()
][:220]
attempts = 0


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /private\n"


@app.post("/reset")
def reset():
    global attempts
    attempts = 0
    return {"reset": True}


@app.get("/", response_class=HTMLResponse)
async def root():
    await asyncio.sleep(0.015)
    return "<title>Local CPython mirror</title><h1>Дзеркало документації Python</h1>" + "".join(
        f'<a href="/page/{i}">Document {i}</a>' for i in range(220)
    )


@app.get("/page/{doc_id}", response_class=HTMLResponse)
async def page(doc_id: int):
    global attempts
    await asyncio.sleep(0.015)
    if doc_id == 0 and attempts == 0:
        attempts += 1
        return HTMLResponse("Temporary limit", status_code=429, headers={"Retry-After": "0"})
    doc = docs[doc_id % len(docs)]
    return (
        "<title>"
        + html.escape(doc["title"])
        + "</title><article>"
        + html.escape(doc["text"])
        + "</article>"
    )
