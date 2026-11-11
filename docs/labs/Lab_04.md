# Лабораторна робота №4. Типи, тести, пакування та CLI

## Мета

Підготувати типізований і протестований Python-пакунок із командним інтерфейсом.

## Виконання та реалізація

Типізовано публічний API, налаштовано Pyright strict, Mypy та Ruff. Перевірено fixtures, Hypothesis і CLI; зібрано wheel і виконано встановлення в окреме середовище.

## Команди запуску

```powershell
uv sync --frozen
uv run findex --help
uv run pytest --cov=findex
uv run pyright
uv build
```

## Лабораторна 4. Типи, тестування, пакування і CLI

Публічні функції типізовано; рушії мають Literal у внутрішньому API та Enum на межі Typer. Протокол Scorer не потребує успадкування. JSON Lines надходять лише у stdout; діагностика — stderr. Зібраний wheel перевірено встановленням через uv tool в окреме середовище. Віддалений статус CI не видається за перевірений.

| Перевірка | Результат |
|---|---|
| pytest на етапі 4 | 58 passed |
| Покриття на етапі 4 | 80% |
| pyright strict | 0 errors |
| mypy strict | 0 errors |
| ruff | check / format пройдено |
| Wheel | findex-0.4.0-py3-none-any.whl; встановлено uv tool у чисте середовище |
| GitHub Actions | [Запуск 43021534036: success](https://github.com/editlikeorigin-afk/findex-python-labs/actions/runs/43021534036), SHA b02d1be; статус перевірено 11.11.2026 |
| GitHub Release v0.4.0 | Пакет підготовлено; опублікований Release поки відсутній |

## Висновок

Типізовано API, реалізовано CLI та виконано автоматизовані перевірки. Встановлення wheel підтвердило працездатність точки входу. GitHub Actions завершився успішно; пакет v0.4.0 підготовлено, але Release та встановлення за його URL ще не перевірено.

## Reflection

1. CPython не перевіряє відповідність runtime-значень type hints. Їх читають Pyright/Mypy,
   IDE та бібліотеки на кшталт Typer/FastAPI/Pydantic. Перевірка запускається інструментами/CI.
2. Для `x: str | None` виклик x.upper() небезпечний; `if x is None: return ''`
   звужує тип у наступній гілці до str.
3. Аргумент зазвичай приймається як Iterable, якщо достатньо for; generator повертає Iterator,
   щоб контракт дозволяв next. Якщо потрібен саме next на вході, тип входу теж Iterator.
4. Pyright порівнює сигнатуру `score(term, posting, index) -> float` з Protocol Scorer.
   TfIdf і BM25 відповідають структурно, без успадкування від Scorer.
5. Session fixture спільна для набору; мутація індексу одним тестом може зіпсувати інші.
   Потрібна незмінність або fixture з меншим scope/незалежною копією.
6. Властивість: merge_and для довільних відсортованих унікальних списків дорівнює sorted(set(a)&set(b)).
   Shrinking знаходить найменший контрприклад, а не лишає довгий випадковий ввід.
7. `src/` не дозволяє випадково тестувати кореневу папку замість інстальованого пакета;
   помилки packaging/entry point проявляються раніше.
8. Installer читає console_scripts entry point і створює командний launcher `findex`
   у bin/Scripts середовища, який імпортує `findex.cli:app`.
9. `%`-аргументи передаються logger окремо й форматуються тільки за активного рівня.
   F-string обчислюється завжди; це зайва робота для вимкнених повідомлень.

## Джерела

[Методичка](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-04-typing-testing-packaging-cli.md) і відповідний файл notes.
