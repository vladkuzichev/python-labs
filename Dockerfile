FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.13-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim
RUN useradd --create-home --uid 10001 findex
WORKDIR /app
COPY --from=builder --chown=findex:findex /app /app
ENV PATH="/app/.venv/bin:$PATH" INDEX_PATH="/data/index.bin" PYTHONUNBUFFERED=1
USER findex
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["findex", "serve", "--host", "0.0.0.0", "--port", "8000"]
