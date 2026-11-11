# Захист лабораторної №1

## Команди

```powershell
uv sync --frozen
uv run python scripts/prepare_corpus.py
uv run python -m findex.stats data/stdlib.jsonl
uv run python -m findex.stats data/stdlib.jsonl --eager
```

## Reflection

1. `for` отримує `it = iter(xs)`, повторює `next(it)` і завершується на `StopIteration`.
   Iterable видає ітератор; iterator містить позицію й `__next__`; generator object — iterator.
2. Список повертає новий ітератор кожного разу. Генератор одноразовий; для нового проходу
   викликається його функція знову, а не «перемотується» старий об'єкт.
3. У pipeline в пам'яті є поточний документ, поточний токен і `Counter` вже знайдених термінів.
   Словник зростає зі словником корпусу; лінивість не означає нульову пам'ять.
4. Помилка в тілі генератора виникає під час `next`/споживання, а не під час створення generator object.
5. `Straße`.casefold() дає `strasse`, тоді як lower лишає ß. NFC зрівнює `é` та `e` + combining acute.
6. `findall` матеріалізує всі збіги; `finditer` видає їх по одному. Вихідний рядок усе одно лишається в пам'яті.
7. Eager зберігає документи та списки токенів разом із Counter. Lazy — документ і Counter.
   Початковий пік 12445233 проти 1635543 байтів стосується конкретного запуску.
