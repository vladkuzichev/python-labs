from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal, cast

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from findex.index import Index
from findex.retrieval import SearchMode, retrieve
from findex.search import candidate_ids
from findex.store import load
from findex.web.models import DocumentOut, ResultOut, SearchResponse, StatsOut
from findex.web.settings import Settings

logger = logging.getLogger(__name__)
ScorerName = Literal["bm25", "tfidf"]
here = Path(__file__).parent
templates = Jinja2Templates(directory=here / "templates")


def get_index(request: Request) -> Index:
    index = cast(Index | None, getattr(request.app.state, "index", None))
    if index is None:
        raise HTTPException(503, "Індекс ще не завантажено")
    return index


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def execute(
    index: Index,
    q: str,
    k: int,
    scorer: ScorerName,
    page: int,
    mode: SearchMode = "keyword",
    settings: Settings | None = None,
) -> SearchResponse:
    started = time.perf_counter()
    try:
        total = len(candidate_ids(index, q)) if mode == "keyword" else index.num_docs
        config = settings or Settings()
        ranked = retrieve(
            index,
            q,
            k=min(k * page, index.num_docs or 1),
            scorer=scorer,
            mode=mode,
            backend=config.backend,
            embeddings_path=config.embeddings_path,
            model_path=config.model_path,
        )
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except OSError as error:
        logger.error("semantic_load_failed error=%s", error)
        raise HTTPException(503, "Семантичний індекс не підготовлено") from error
    selected = ranked[(page - 1) * k : page * k]
    return SearchResponse(
        query=q,
        total=total,
        took_ms=(time.perf_counter() - started) * 1000,
        results=[ResultOut.model_validate(r) for r in selected],
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.started = time.perf_counter()
        application.state.index = None
        # Тести підставляють залежність перед lifespan: реальний файл їм не потрібен.
        if get_index not in application.dependency_overrides:
            try:
                application.state.index = await asyncio.to_thread(load, config.index_path)
            except (OSError, ValueError, EOFError) as error:
                logger.error("index_load_failed path=%s error=%s", config.index_path, error)
        yield
        index = application.state.index
        if index is not None:
            index.close()

    application = FastAPI(title="findex", version="1.0.0", lifespan=lifespan)
    application.state.settings = config
    application.state.index = None
    application.state.started = time.perf_counter()
    application.mount("/static", StaticFiles(directory=here / "static"), name="static")

    async def request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", "")
        if not re.fullmatch(r"[a-zA-Z0-9-]{1,64}", request_id):
            request_id = uuid.uuid4().hex
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unexpected_error request_id=%s path=%s", request_id, request.url.path)
            response = JSONResponse(
                {"detail": "Внутрішня помилка сервера", "request_id": request_id}, status_code=500
            )
        response.headers["X-Request-ID"] = request_id
        return response

    def search_route(
        q: Annotated[str, Query(min_length=1, max_length=1000)],
        index: Annotated[Index, Depends(get_index)],
        settings: Annotated[Settings, Depends(get_settings)],
        k: Annotated[int, Query(ge=1, le=100)] = 10,
        scorer: ScorerName = "bm25",
        page: Annotated[int, Query(ge=1, le=10000)] = 1,
        mode: SearchMode = "keyword",
    ) -> SearchResponse:
        return execute(index, q, k, scorer, page, mode, settings)

    async def search_async(
        q: Annotated[str, Query(min_length=1, max_length=1000)],
        index: Annotated[Index, Depends(get_index)],
        settings: Annotated[Settings, Depends(get_settings)],
        k: Annotated[int, Query(ge=1, le=100)] = 10,
        scorer: ScorerName = "bm25",
        page: Annotated[int, Query(ge=1, le=10000)] = 1,
        mode: SearchMode = "keyword",
    ) -> SearchResponse:
        # Лише контрольний режим benchmark: демонструє блокування CPU-роботою.
        return execute(index, q, k, scorer, page, mode, settings)

    application.add_api_route(
        "/search",
        search_route if config.route_style == "sync" else search_async,
        methods=["GET"],
        response_model=SearchResponse,
    )

    @application.get("/docs/{doc_id}", response_model=DocumentOut)
    def document(doc_id: int, index: Annotated[Index, Depends(get_index)]) -> DocumentOut:
        if doc_id not in index.doc_meta:
            raise HTTPException(404, "Документ не знайдено")
        meta = index.doc_meta[doc_id]
        return DocumentOut(doc_id=doc_id, path=meta.path, title=meta.title, text=meta.text)

    def health(index: Annotated[Index, Depends(get_index)]) -> dict[str, str]:
        return {"status": "ok"}

    def stats(
        request: Request,
        index: Annotated[Index, Depends(get_index)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> StatsOut:
        return StatsOut(
            documents=index.num_docs,
            vocabulary=len(index),
            tokens=sum(index.doc_lengths.values()),
            index_bytes=settings.index_path.stat().st_size if settings.index_path.exists() else 0,
            uptime_s=time.perf_counter() - cast(float, request.app.state.started),
        )

    def home(
        request: Request,
        index: Annotated[Index, Depends(get_index)],
        q: Annotated[str, Query(max_length=1000)] = "",
        page: Annotated[int, Query(ge=1, le=10000)] = 1,
        scorer: ScorerName = "bm25",
        mode: SearchMode = "keyword",
    ) -> Response:
        result = execute(index, q, 5, scorer, page, mode, config) if q.strip() else None
        return templates.TemplateResponse(
            request=request,
            name="search.html",
            context={
                "result": result,
                "q": q,
                "page": page,
                "scorer": scorer,
                "mode": mode,
                "documents": index.num_docs,
            },
        )

    def document_page(
        request: Request, doc_id: int, index: Annotated[Index, Depends(get_index)]
    ) -> Response:
        result = document(doc_id, index)
        return templates.TemplateResponse(
            request=request, name="document.html", context={"document": result}
        )

    application.middleware("http")(request_id)
    application.add_api_route("/health", health, methods=["GET"])
    application.add_api_route("/stats", stats, methods=["GET"], response_model=StatsOut)
    application.add_api_route("/", home, methods=["GET"], response_class=HTMLResponse)
    application.add_api_route(
        "/doc/{doc_id}", document_page, methods=["GET"], response_class=HTMLResponse
    )
    return application


app = create_app()
