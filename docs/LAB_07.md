# Лабораторна робота №7. Вебпошук на FastAPI

## Мета

Надати пошук через валідований HTTP API і вебінтерфейс та виміряти локальне навантаження.

## Виконання та реалізація

Реалізовано search/docs/stats/health, lifespan, Pydantic settings та Jinja UI. Перевірено статуси 400/404/422/503, пагінацію, def/async def і локальні конфігурації workers.

## Команди запуску

```powershell
uv sync --frozen
uv run python scripts/prepare_corpus.py
uv run findex index data/stdlib.jsonl --positions --out data/index.bin
$env:INDEX_PATH = "data/index.bin"
uv run findex serve --port 8010
```

## Лабораторна 7. Вебпошук: FastAPI, Pydantic та вебінтерфейс

oha 1.16.0 надсилав по 1000 справжніх HTTP-запитів з concurrency=50. Окремий дослід надсилав 20 запитів одночасно через httpx. Для oha SSL_CERT_FILE указував на certifi, оскільки читання системного сховища сертифікатів було недоступне; налаштування Windows не змінювалися. Чотири процеси розділяють GIL, але кожен завантажує власний індекс.

| Конфігурація | RPS | p50, мс | p95, мс | p99, мс | 20 запитів, с |
|---|---|---|---|---|---|
| local-sync-1 | 533.22 | 91.945 | 115.244 | 201.575 | 0.058495 |
| local-async-1 | 481.50 | 101.303 | 121.269 | 234.076 | 0.051180 |
| local-sync-4 | 1817.43 | 25.146 | 35.627 | 43.28 | 0.034062 |

## Висновок

Реалізовано API та вебінтерфейс, перевірено маршрути й локальне навантаження. Порівняно def, async def та кілька процесів. Docker build/run, публічний сервіс і deployed-вимірювання ще не перевірено.

## Reflection

1. Uvicorn обробляє HTTP і ASGI, Starlette маршрутизує/middleware, FastAPI розв'язує
   dependencies та параметри, Pydantic валідує межу, після handler формується JSON/HTML-відповідь.
2. WSGI описує синхронний request/response callable; ASGI підтримує async messages,
   lifespan і довгі з'єднання. Це не робить блокуючий handler неблокуючим автоматично.
3. FastAPI читає анотацію та Query-обмеження, Pydantic перевіряє `k` і генерує 422/detail
   до виклику маршруту. Анотації тут мають runtime-споживача, як у Typer.
4. Pydantic перевіряє недовірені параметри/JSON/settings; dataclass — внутрішні Posting/DocMeta.
   Тотальна runtime-валідація всіх постінгів додала б наклад без потреби.
5. Depends викликає dependency й передає результат handler. У тесті
   `app.dependency_overrides[get_index] = ...` надає tiny index без справжнього файла.
6. Для синхронного пошуку використано def, який FastAPI запускає в thread pool.
   Async def без await/offload блокує loop. Thread pool не прибирає GIL для Python CPU.
7. Той самий image отримує різні шляхи/ресурси з environment, без редагування коду.
   `.env` — локальний спосіб передавання settings, він не відстежується Git.
8. Кілька процесів мають окремі GIL і можуть скоротити чергу; натомість кожен тримає
   власний індекс і витрачає RAM. У початковому досліді p99 скоротився з 201.575 до 43.28 мс.
9. Health має перевіряти готовність індексу, а не лише роботу HTTP. 503 сигналізує
   неготовність; конкретна реакція платформи залежить від health-check налаштувань і ще не перевірена deployment.

## Джерела

[Методичка](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-07-fastapi-web-search.md) і відповідний файл notes.
