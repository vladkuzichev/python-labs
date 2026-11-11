FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.13-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY scripts ./scripts
COPY evaluation ./evaluation
RUN uv sync --frozen --no-dev --no-editable
# A Git clone intentionally has no data/ or models/. Build the corpus and index
# inside this image instead of COPYing files that are absent from the repository.
RUN uv run --no-sync python scripts/prepare_corpus.py
RUN uv run --no-sync findex index data/stdlib.jsonl --positions --out data/index.npz
ARG WITH_SEMANTIC=0
RUN mkdir -p models/all-MiniLM-L6-v2 data/embeddings && \
    if [ "$WITH_SEMANTIC" = "1" ]; then \
      uv run --no-sync python scripts/download_model.py && \
      uv run --no-sync findex embed data/index.npz --out data/embeddings; \
    fi

FROM python:3.13-slim
RUN useradd --create-home --uid 10001 findex
WORKDIR /app
COPY --from=builder --chown=findex:findex /app /app
ENV PATH="/app/.venv/bin:$PATH" INDEX_PATH="/app/data/index.npz" PYTHONUNBUFFERED=1
ENV MODEL_PATH="/app/models/all-MiniLM-L6-v2" EMBEDDINGS_PATH="/app/data/embeddings"
USER findex
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["findex", "serve", "--host", "0.0.0.0", "--port", "8000"]
