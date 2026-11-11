# Захист лабораторної №3

## Команди

```powershell
uv sync --frozen
uv run python scripts/prepare_corpus.py
uv run python -m findex.index data/stdlib.jsonl --positions --out data/index.bin
uv run python -m findex.search data/index.bin '"event loop" OR asyncio'
```

## Reflection

1. `term in index` використовує контейнерний протокол `__contains__`; `len` — `__len__`
   через тип об'єкта. Built-ins забезпечують семантику й перевірки, їх варто викликати замість dunder вручну.
2. Protocol перевіряє наявність і сумісність членів структурно. ABC задає номінальний інтерфейс
   з успадкуванням і може забороняти інстанціювання неповної реалізації.
3. `timed(fn)` повертає wrapper, який вимірює `perf_counter`, у `finally` логує час і має
   `@wraps(fn)`. Без wraps губляться ім'я, документація та `__wrapped__` для introspection.
4. `retry(times)` повертає decorator; decorator отримує fn і повертає wrapper з циклом спроб.
   Це три рівні: параметри декоратора → функція → виклик функції.
5. До yield відбувається enter, після yield — exit. Виняток із тіла with вводиться в генератор;
   `finally` виконує cleanup і на return, і на помилці. У findex `open_index` викликає `close`.
6. BM25 насичує TF і нормалізує довжину. `k1` керує насиченням, `b` — штрафом за довжину;
   при b=0 довжина не впливає на знаменник.
7. Для малого k `heapq.nlargest` потребує O(N log k), повне сортування — O(N log N).
   На малих N наклад може нівелювати різницю; результати мають детермінований tie-break.
8. Парсер має вищий пріоритет AND за OR, тому `a OR b c` дає `Or(a, And(b,c))`.
   Окремі рівні recursive descent реалізують цей пріоритет, а тести порівнюють дерева.
