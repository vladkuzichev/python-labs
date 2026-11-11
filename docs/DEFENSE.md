# Захист лабораторної №6

## Команди

```powershell
uv sync --frozen
uv run uvicorn scripts.mirror:app --port 8766
uv run findex crawl http://127.0.0.1:8766/ --max-pages 200 --concurrency 5 --out data/crawl.jsonl
uv run findex index data/crawl.jsonl --out data/crawled.bin
```

## Reflection

1. На await мережевого вводу task призупиняється; loop запускає готові task,
   а механізм ОС повідомляє про готовність I/O (на Windows реалізація відрізняється від Unix selectors).
2. Cooperative перемикається на await, preemptive може перервати потік. В asyncio немає
   перемикання між двома звичайними інструкціями без await, але інваріант через await теж потребує захисту.
3. `time.sleep` блокує потік loop і всіх workers. `await asyncio.sleep` реєструє таймер
   і повертає керування; блокуючий виклик можна винести в `asyncio.to_thread`.
4. Виклик async def створює coroutine object; виконання починається при await або scheduling Task.
   Це схоже на відкладене виконання генератора, але consumer тут планувальник.
5. TaskGroup утримує дочірні задачі у спільному scope; звичайний збій скасовує siblings
   і піднімає згруповані помилки як ExceptionGroup. Gather має іншу семантику за замовчуванням.
6. Crawl перекриває мережеве очікування, index витрачає CPU. До того ж у справжньому
   локальному досліді concurrency=5 була швидша за 20; універсальна перевага 20 не стверджується.
7. CancelledError успадковує BaseException, тому звичайний `except Exception` його не ловить.
   Небезпечно ковтати BaseException/CancelledError без повторного raise; cleanup має відбутися у finally.
8. Global semaphore обмежує всі запити, per-host — навантаження на конкретний host.
   Retry-After задає серверний час очікування, який враховується замість довільного негайного retry.
9. CPU-індексація виконується після crawl; за необхідності під час обходу — окремий process executor.
   Thread доречний для блокуючого I/O/створення SSL-клієнта, але не гарантує CPU-паралелізм Python.
