# Захист лабораторної №7

## Команди

```powershell
uv sync --frozen
uv run python scripts/prepare_corpus.py
uv run findex index data/stdlib.jsonl --positions --out data/index.bin
$env:INDEX_PATH = "data/index.bin"
uv run findex serve --port 8010
```

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
