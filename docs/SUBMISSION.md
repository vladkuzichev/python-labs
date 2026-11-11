# Здача лабораторних робіт 1–8

Аудит 11.11.2026. Перевірено локальний проєкт, опубліковані refs та GitHub Actions,
8 оригінальних завдань, 8 notes, README курсу й 8 початкових Classroom-скриншотів.
Жодна методичка не відсутня. Локальні копії відрізняються від поточних GitHub blobs лише
доданим кінцевим newline: усі 17 звірок пройдено, [доказ](evidence/methods-check.json).
Файли викладача зберігаються окремо в `READY_TO_SUBMIT/Documentation/SourceMaterials/`.
Варіанти у цих завданнях відсутні; №11 не призначався.

Статуси «виконано» нижче стосуються перевірених матеріалів main, якщо явно не названо тег.
«Частково» означає реальний незакритий пункт; «не застосовується» — вимога цього етапу відсутня.
Підготовлений конфіг, пакет чи навчальна відповідь не означають виконане розгортання,
опублікований Release або складений усний захист. Повної відповідності всіх восьми робіт не заявлено.

## Оригінальні джерела

| № | Повне завдання викладача | Додаткові notes |
|---|---|---|
| 01 | [Iterators and corpus](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-01-iterators-and-the-corpus.md) | [Notes 01](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-01-iterators-and-the-corpus.notes.md) |
| 02 | [Data structures and inverted index](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-02-data-structures-and-the-inverted-index.md) | [Notes 02](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-02-data-structures-and-the-inverted-index.notes.md) |
| 03 | [Object model and ranking](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-03-the-object-model-and-ranking.md) | [Notes 03](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-03-the-object-model-and-ranking.notes.md) |
| 04 | [Typing, testing, packaging, CLI](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-04-typing-testing-packaging-cli.md) | [Notes 04](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-04-typing-testing-packaging-cli.notes.md) |
| 05 | [Concurrency and GIL](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-05-concurrency-and-the-gil.md) | [Notes 05](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-05-concurrency-and-the-gil.notes.md) |
| 06 | [Asyncio crawler](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-06-asyncio-crawler.md) | [Notes 06](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-06-asyncio-crawler.notes.md) |
| 07 | [FastAPI web search](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-07-fastapi-web-search.md) | [Notes 07](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-07-fastapi-web-search.notes.md) |
| 08 | [Performance and semantic search](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-08-performance-and-semantic-search.md) | [Notes 08](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/lab-08-performance-and-semantic-search.notes.md) |

[README курсу](https://github.com/rmalkevy/Programming-Practice-Projects/blob/main/courses/python/README.md)
встановлює спільний findex, src-layout, тег на кожен етап і п'ятихвилинний захист.
Classroom №4 конкретно вимагає Pyright strict: виконано його, додатково Mypy.
Notes №7 радять падіння startup без індексу, а Classroom №7 вимагає `/health` 503;
обрано конкретну вимогу Classroom: сервер логуює помилку й відповідає 503 без індексу.
У №8 семантична гілка альтернативна глибокому memmap/gap-encoding досліду; реалізовано семантичну,
тому 10×-корпус для альтернативної гілки не позначається обов'язковим.
Звіти DOCX здаються окремими файлами.

## Матриця вимог і доказів

| Лабораторна | Вимога | Файл або посилання | Статус |
|---|---|---|---|
| 01 | ≥1000 документів АБО ~50 МБ, джерело і data/ ignored | [corpus manifest](measurements/corpus_manifest.json), [prepare_corpus](../scripts/prepare_corpus.py), [.gitignore](../.gitignore) | Виконано: історично 2873 docstring; новий корпус залежить від Python |
| 01 | Lazy document stream, NFC/casefold/finditer, policy | [corpus.py](../src/findex/corpus.py), [tokenize.py](../src/findex/tokenize.py), [README](../README.md) | Виконано; TXT tree або JSONL-файл; JSONL слід передавати шляхом до файла |
| 01 | Однопрохідна stats, top50, limit/islice, tracemalloc | [stats.py](../src/findex/stats.py) | Виконано |
| 01 | Тести mixed case, кирилиця, combining mark, punctuation, empty | [test_tokenize](../tests/test_tokenize.py) | Виконано |
| 01 | Eager/lazy таблиця та пояснення пам'яті | [README](../README.md), [lazy](measurements/lab01_lazy.json), [eager](measurements/lab01_eager.json) | Виконано; таблиця є і в lab-01 |
| 01 | Тег, звіт, Reflection | [lab-01](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-01), `Reports/Lab_01.docx` окремо, [Reflection](DEFENSE.md#lab-01) | Тег перевірено; DOCX оновлено; усний захист ще не відбувся |
| 01 | Release / deployment | Оригінальне завдання №1 | Не застосовується |
| 02 | Frozen/slotted/hashable Posting і DocMeta; single-pass defaultdict, lengths/meta | [index.py](../src/findex/index.py), [tests](../tests/test_index.py) | Виконано |
| 02 | Merge AND/OR/NOT, set engine, часті/рідкі терміни | [boolean.py](../src/findex/boolean.py), [search.py](../src/findex/search.py), [JSON](measurements/lab02_measurements.json) | Код і вимірювання виконано; таблиць немає саме в lab-02 |
| 02 | Pickle+JSON, file size/save/load, пояснення небезпеки | [store.py](../src/findex/store.py), [MEASUREMENTS](MEASUREMENTS.md) | Виконано в main; історичний README lab-02 неповний |
| 02 | Plain/slots/array table і cost positions | [measure_lab02.py](../scripts/measure_lab02.py), [JSON](measurements/lab02_measurements.json), [README](../README.md) | Виконано в main; таблиця plain/slots/array вперше у lab-03 |
| 02 | Модульні CLI та тести round-trip/merge | [index.py](../src/findex/index.py), [search.py](../src/findex/search.py), [tests](../tests/test_index.py) | Виконано |
| 02 | Тег, звіт, Reflection | [lab-02](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-02), `Reports/Lab_02.docx` окремо, [Reflection](DEFENSE.md#lab-02) | Тег збережено; недолік README наведено нижче |
| 02 | Release / deployment | Оригінальне завдання №2 | Не застосовується |
| 03 | Index dunders, cached_property, context manager | [index.py](../src/findex/index.py), [store.py](../src/findex/store.py) | Виконано |
| 03 | Scorer protocol, BM25/TF-IDF, heapq top-k | [scoring.py](../src/findex/scoring.py), [search.py](../src/findex/search.py) | Виконано |
| 03 | 3 sanity checks на повному корпусі | [sanity_corpus.py](../scripts/sanity_corpus.py), [JSON](measurements/lab03_sanity_corpus.json), [README](../README.md) | Виконано в main; в lab-03 були fixture-тести, а не повна таблиця корпусу |
| 03 | AST, operators, phrases, tree-equality tests | [query.py](../src/findex/query.py), [tests](../tests/test_query_ranking.py) | Виконано |
| 03 | timed/wraps, lru_cache, snippets, log повторного query | [instrument.py](../src/findex/instrument.py), [cache log](evidence/historical/lab03_cache.log) | Виконано |
| 03 | 10 hand-labeled queries та P@5 | [qrels](../evaluation/qrels.json), [table](measurements/lab03_precision.json) | Частково: обчислення є, розмітка неповна; незалежна перевірка людиною відсутня |
| 03 | Тег, звіт, Reflection | [lab-03](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-03), `Reports/Lab_03.docx` окремо, [Reflection](DEFENSE.md#lab-03) | Матеріали підготовлено; критерій ручної розмітки не закрито |
| 03 | Release / deployment | Оригінальне завдання №3 | Не застосовується |
| 04 | Typed API, Protocol, strict checker, justified ignores | [pyproject](../pyproject.toml), [scoring](../src/findex/scoring.py), [validation](VALIDATION.md) | Виконано: Pyright і Mypy пройдено |
| 04 | ≥30 tests, ≥3 properties, fixture/CLI/coverage | [tests/](../tests/), [properties](../tests/test_properties_cli.py), [validation](VALIDATION.md) | Виконано; історично 58 тестів №4, фінально 103 до виправлення crawler |
| 04 | Typer/Rich, JSONL/stdout, logging/stderr, expected error exit | [cli.py](../src/findex/cli.py), [CLI tests](../tests/test_properties_cli.py) | Виконано |
| 04 | src-layout, uv.lock, wheel, isolated install | [pyproject](../pyproject.toml), [uv.lock](../uv.lock), [validation](VALIDATION.md) | Виконано локально |
| 04 | GitHub CI green та badge | [Actions](https://github.com/editlikeorigin-afk/findex-python-labs/actions/runs/43021534036), [README](../README.md) | Виконано для b02d1be; lab-04 не має свого історичного green run або badge |
| 04 | GitHub Release v0.4.0 з wheel та install-from-release | [RELEASES](RELEASES.md), [готовий опис](releases/v0.4.0.md) | Частково: пакет перевірено локально, Release не опубліковано; URL-install не виконано |
| 04 | Тег, звіт, Reflection | [lab-04](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-04), [v0.4.0](https://github.com/editlikeorigin-afk/findex-python-labs/tree/v0.4.0), `Reports/Lab_04.docx`, [Reflection](DEFENSE.md#lab-04) | Теги перевірено; Release є окремою незакритою вимогою |
| 04 | Deployment вебсервісу | Оригінальне завдання №4 | Не застосовується |
| 05 | build_partial/merge, paths, unique IDs, identical serial/parallel | [parallel.py](../src/findex/parallel.py), [tests](../tests/test_parallel.py) | Виконано; JSONL потоково розбивається у тимчасові файли |
| 05 | 3 executors, workers, spawn-safe, worker failures | [cli.py](../src/findex/cli.py), [parallel.py](../src/findex/parallel.py) | Виконано |
| 05 | 1/2/4/8/all ×3 executors ×≥3 runs, CPU/RSS/merge | [JSON](measurements/lab05_parallel.json), [machine](measurements/machine.json), [table](../README.md) | Виконано; RSS батька, не сума всіх процесів |
| 05 | Plot PNG, ideal line, one-page GIL explanation | [plot](parallel_speedup.png), [GIL](GIL.md) | Виконано; README main також містить зображення графіка |
| 05 | CPython 3.13t, gil_enabled=False, interpretation | [free-threaded JSON](measurements/lab05_free_threaded.json), [GIL](GIL.md) | Виконано; гонку не спостерігали; serial лишився default за результатом |
| 05 | Тег, звіт, Reflection | [lab-05](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-05), `Reports/Lab_05.docx`, [Reflection](DEFENSE.md#lab-05) | Підготовлено; усний захист окремо |
| 05 | Release / deployment | Оригінальне завдання №5 | Не застосовується; I/O counter-benchmark є optional |
| 06 | timeout/retry/jitter/Retry-After, robots, honest UA, MockTransport | [fetch](../src/findex/crawler/fetch.py), [robots](../src/findex/crawler/robots.py), [tests](../tests/test_crawler.py) | Виконано для дозволеного власного локального дзеркала |
| 06 | Queue/TaskGroup, semaphores/delay, canonicalization/seen, budget/cleanup | [crawl.py](../src/findex/crawler/crawl.py) | Виконано |
| 06 | Async generator → streaming JSONL → index, Rich stats/log | [cli](../src/findex/cli.py), [mirror](../scripts/mirror.py), [historical log](evidence/historical/lab06_crawl_excerpt.log) | Виконано |
| 06 | Неблокуючий цикл, debug=True clean | [crawl.py](../src/findex/crawler/crawl.py), [regression test](../tests/test_crawler.py), [validation](VALIDATION.md) | Startup warning історично був; у main ініціалізацію клієнта винесено в to_thread і повторено debug-сценарій |
| 06 | ≥200 pages, concurrency 1/5/20, оброблений збій у логах | [JSON](measurements/lab06_benchmark.json), [429 log](evidence/historical/lab06_crawl_excerpt.log), [README](../README.md) | Виконано; 5 швидше за 20, цифри збережено |
| 06 | Тег, звіт, Reflection | [lab-06](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-06), `Reports/Lab_06.docx`, [Reflection](DEFENSE.md#lab-06) | Тег збережено; startup-fix знаходиться лише в наступному main |
| 06 | Release / deployment | Оригінальне завдання №6 | Не застосовується |
| 07 | /search, /docs/{id}, /stats, /health, validation/pagination/OpenAPI | [web/app.py](../src/findex/web/app.py), [models](../src/findex/web/models.py) | Виконано локально |
| 07 | Lifespan/Depends/settings, errors/request_id, overrides tests | [settings](../src/findex/web/settings.py), [tests](../tests/test_web.py) | Виконано; success/422/404/503 покрито |
| 07 | Jinja/static UI, highlight/pagination/document | [templates](../src/findex/web/templates/), [GIF](demo.gif) | Виконано локально |
| 07 | 20 concurrent sync/async timings та local oha ×3 | [load JSON](measurements/lab07_load.json), [oha JSON](measurements/lab07_oha_local-sync-1.json), [README](../README.md) | Виконано локально; це не hosted numbers |
| 07 | Multi-stage Docker non-root, build/run | [Dockerfile](../Dockerfile), [DEPLOYMENT](DEPLOYMENT.md) | Конфіг виправлено для clean clone; виконання не перевірене, Docker відсутній |
| 07 | Public URL, platform health/logs, deployed oha | [render.yaml](../render.yaml), [DEPLOYMENT](DEPLOYMENT.md) | Не виконано: немає доступного налаштованого хостингу/публічного сервісу |
| 07 | Тег, version 0.7.0, звіт, Reflection | [lab-07](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-07), [v0.7.0](https://github.com/editlikeorigin-afk/findex-python-labs/tree/v0.7.0), `Reports/Lab_07.docx`, [Reflection](DEFENSE.md#lab-07) | Версію/теги перевірено; повна готовність заблокована deployment |
| 07 | GitHub Release | Оригінальне завдання №7 | Окремий Release не вимагається; version/tag — вимагаються |
| 08 | cProfile+py-spy index/search, SVG, top3/hypotheses | [hotspots](hotspots_before.md), [index SVG](index-before.svg), [search SVG](search-before.svg) | Основні профілі є |
| 08 | Scalene Python/native для всіх hotspot | [Scalene](SCALENE.md), [JSON](measurements/lab08_scalene_breakdown.json) | Частково: у початковому профілі build_index/tokenize не засемпльовано; додатковий запуск засемплював build_index, але не tokenize |
| 08 | int32 postings/doc_len, vector BM25/TF-IDF, argpartition, same ranking | [vector.py](../src/findex/vector.py), [tests](../tests/test_vector_semantic.py) | Виконано |
| 08 | ≥3 queries speedup table, small-list explanation | [speed JSON](measurements/lab08_speed.json), [README](../README.md) | Виконано; без зміни початкових чисел |
| 08 | build/search pytest-benchmark in CI | [benchmark tests](../tests/test_benchmark.py), [workflow](../.github/workflows/ci.yml), [CI](https://github.com/editlikeorigin-afk/findex-python-labs/actions/runs/43021534036) | Виконано; грубий поріг mean:99% задокументовано |
| 08 | Chunks/MiniLM/L2/.npy/best chunk, RRF, modes CLI/API/UI | [semantic](../src/findex/semantic.py), [retrieval](../src/findex/retrieval.py), [manifest](../evaluation/model_manifest.json) | Виконано; завантаження/побудова окремими командами |
| 08 | 10+5 queries, no word-overlap paraphrases, P@5 | [qrels_15](../evaluation/qrels_15.json), [precision JSON](measurements/lab08_precision.json), [README](../README.md) | Обчислено; попередні qrels потребують ручної перевірки |
| 08 | README first screen, all measurements, diagram, GIF, 2–3min video | [README](../README.md), [architecture](architecture.png), [GIF](demo.gif), [video](demo.webm) | Виконано, крім live URL; відео 2:55.6, без озвучення |
| 08 | Deployed v1.0.0 | [DEPLOYMENT](DEPLOYMENT.md) | Не виконано; локальна/кодова версія 1.0.0 не дорівнює hosted instance |
| 08 | Теги, звіт, Reflection/showcase | [lab-08](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-08), [v1.0.0](https://github.com/editlikeorigin-afk/findex-python-labs/tree/v1.0.0), `Reports/Lab_08.docx`, [Reflection](DEFENSE.md#lab-08) | Теги перевірено; сценарій підготовлено, усний захист не виконано |
| 08 | GitHub Release | Оригінальне завдання №8 | Потрібні version/tag; окремий Release прямо не зазначений; опис v1.0.0 підготовлено додатково |

## Посилання для Classroom та стан тегів

Виправлені тексти всіх восьми етапів опубліковано в окремих гілках. Теги lab-01–lab-08
поки вказують на попередні коміти: їх оновлення не виконано через недоступність Git-з’єднання.
Версійні теги v0.4.0, v0.7.0 і v1.0.0 залишено без змін. Історію Git збережено.
Для перегляду актуальних текстів слід користуватися гілками в таблиці та документацією main.
[Початкова перевірка вмісту тегів](evidence/tag-audit.json) описує попередні коміти.

| Робота | Тег для здачі | Виправлена версія | Матеріали та обмеження |
|---|---|---|---|
| 01 | [lab-01](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-01) | [text-review/lab-01](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-01) | Корпус, tokenizer і таблиці вимірювань. |
| 02 | [lab-02](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-02) | [text-review/lab-02](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-02) | Додано таблиці №2 з наявних вимірювань. |
| 03 | [lab-03](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-03) | [text-review/lab-03](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-03) | Збережено P@5; розмітка неповна й незалежно людиною не перевірена. |
| 04 | [lab-04](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-04) | [text-review/lab-04](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-04) | CLI, типізація і тести; обов’язковий Release ще не опубліковано. |
| 05 | [lab-05](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-05) | [text-review/lab-05](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-05) | Таблиці, графік, GIL і вимірювання Python 3.13t. |
| 06 | [lab-06](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-06) | [text-review/lab-06](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-06) | Crawler і таблиці; виправлення ініціалізації HTTP-клієнта є в main. |
| 07 | [lab-07](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-07) | [text-review/lab-07](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-07) | API/UI й локальні вимірювання; Docker і публічний сервіс не перевірено. |
| 08 | [lab-08](https://github.com/editlikeorigin-afk/findex-python-labs/tree/lab-08) | [text-review/lab-08](https://github.com/editlikeorigin-afk/findex-python-labs/tree/text-review/lab-08) | NumPy, семантичний пошук і медіа; розгортання та повний Scalene breakdown відсутні. |

## Що здається окремо

1. Вісім DOCX: `READY_TO_SUBMIT/Reports/Lab_01.docx` … `Lab_08.docx`.
   Реквізити звірено з вихідним sample; висновки безособові українською; особисті файли не публікуються.
2. За потреби повний автономний комплект із даними/моделлю/Runtime та журналами `Tests/`;
   він не тотожний GitHub-клону. [Опис розміщення](OFFLINE.md).
3. Для №4 — GitHub Release v0.4.0 із перевіреним wheel та демонстрація встановлення за його URL:
   [пакет/опис](RELEASES.md). Тег v0.4.0 без Release цю вимогу не закриває.
4. Для №7–8 — реальний hosted URL, health/logs і deployed oha після доступу до хостингу.
5. Для №3/8 — людська перевірка relevance judgments; після змін розмітки потрібен новий, окремо
   позначений розрахунок P@5. Початкові результати не підміняються заднім числом.
6. П'ятихвилинний захист і 2–3 Reflection: підготовлено [команди та відповіді](DEFENSE.md),
   проте особисте розуміння й усний виступ не можуть бути підтверджені автоматично.

## Висновок

Було досліджено вимоги всіх восьми етапів. Реалізовано та перевірено відтворення keyword-пошуку,
підготовлено докази CI, матрицю вимог і матеріали захисту. Історію й теги збережено.
Незакритими залишаються публікація Release, розгортання, незалежна перевірка розмітки,
оновлення lab-тегів і повний вибірковий профіль Scalene.
