# Захист лабораторної №4

## Команди

```powershell
uv sync --frozen
uv run findex --help
uv run pytest --cov=findex
uv run pyright
uv build
```

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
