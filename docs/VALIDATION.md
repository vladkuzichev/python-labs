# Перевірки та межі доказів

## GitHub Actions

Для редакції текстів `b8d3526b31f0dcf00b5c06ac21a4fc84a8b7a68d` перевірено
[Actions №43037351425](https://github.com/editlikeorigin-afk/findex-python-labs/actions/runs/43037351425):
`completed / success`. Код і залежності цієї редакції не змінювалися.

Через GitHub API перевірено: [Checks №43021534036](https://github.com/editlikeorigin-afk/findex-python-labs/actions/runs/43021534036),
`completed / success`, main `b02d1be2e94758d80bd902f0db0ca8703cb4e4e5`, 11.11.2026,
завершення 12:35:40 UTC. Усі кроки sync, download_model, Ruff, Pyright, Mypy,
pytest/coverage та benchmark comparison успішні. Збережено [резюме кроків](evidence/github-actions-known.json)
і [стан repo/тегів/Releases до аудиту](evidence/github-before.json).
CI для нового коміту потрібно оцінювати окремо на [сторінці workflow](https://github.com/editlikeorigin-afk/findex-python-labs/actions/workflows/ci.yml).
Результат Windows runner не підтверджує Docker/Linux або cloud deployment.

## Новий чистий локальний clone

11.11.2026 виконано `git clone --no-hardlinks` з того самого локального Git-репозиторію
коміту b02d1be в нову папку. Ні `data/`, ні `models/`, ні `.venv/` до неї не копіювалися.
Середовище: CPython 3.13.18 x64, Windows 11, Ryzen 7 7800X3D; [фактичний stdout](evidence/submission-2026-11-11/environment.log).
Мережеве клонування локально не перевірено; використано окремий клон того самого Git-коміту.

Перший `uv sync --frozen --all-extras --offline` **не пройшов**: у cache не було locked wheel onnxruntime.
Це не записано як успіх. Далі в чистий venv встановлено ті самі pinned packages з окремого
wheelhouse, виконано `uv sync --frozen --all-extras --offline --no-build-isolation` — успішно.
Online `uv sync --frozen` підтверджено окремо саме GitHub Actions вище.
Усі команди та exit codes, включно з невдалими спробами: [checks.json](evidence/submission-2026-11-11/checks.json).

| Перевірка | Фактичний результат | Доказ |
|---|---|---|
| prepare_corpus без готових даних | 2873 документи, 1513665 байтів; SHA збігся для того самого runtime | [stdout](evidence/submission-2026-11-11/prepare-corpus.log) |
| index/search/stats без попереднього індексу | exit 0, непорожній JSONL результат | [index](evidence/submission-2026-11-11/index.log), [search](evidence/submission-2026-11-11/search.log), [stats](evidence/submission-2026-11-11/stats.log) |
| Ruff check / format | exit 0 / exit 0 | [check](evidence/submission-2026-11-11/ruff-check.log), [format](evidence/submission-2026-11-11/ruff-format.log) |
| Pyright strict / Mypy strict | 0 errors / Success | [Pyright](evidence/submission-2026-11-11/pyright.log), [Mypy](evidence/submission-2026-11-11/mypy.log) |
| pytest | 103 passed, 86.564% line coverage | [log](evidence/submission-2026-11-11/pytest.log), [JUnit](evidence/submission-2026-11-11/pytest-junit.xml), [coverage](evidence/submission-2026-11-11/coverage.json) |
| Модель | скопійована окремо після keyword-перевірки; SHA256 усіх файлів пройшов | [log](evidence/submission-2026-11-11/model-sha256-offline.log) |
| pytest-benchmark comparison | exit 0, поріг mean:99% | [log](evidence/submission-2026-11-11/benchmark-regression.log) |
| Lock / build / isolated wheel | exit 0, wheel/sdist, findex --help поза клоном | [lock](evidence/submission-2026-11-11/lock.log), [build](evidence/submission-2026-11-11/build.log), [install](evidence/submission-2026-11-11/wheel-install.log), [help](evidence/submission-2026-11-11/wheel-help.log) |

Для локальної перевірки модель надано з автономного комплекту: використано перевірену
копію автономного комплекту. У CI команда справжнього download_model завершилась успішно.
Окремі подальші CLI/HTTP/semantic перевірки та перевірки посилань зберігаються в цьому ж каталозі evidence.

## Початкові локальні вимірювання

[MEASUREMENTS](MEASUREMENTS.md) і [measurements/](measurements/) містять початкові цифри
10–11.11.2026. Вони не замінюються новими timings із тестових журналів.
Попередні локальні знімки: lab-05 — 63, lab-06 — 74, lab-07 — 85 тестів.
Це історичні набори, а не додаткові унікальні тести до 103 фінальних.
Scalene запускалось через subprocess зі справжнім exit 0;
[доказ](measurements/scalene_native_exit.json). Cache hit: [справжній лог](evidence/historical/lab03_cache.log).

## Звіти та непідтверджені можливості

Вісім DOCX перевірено локально: ZIP CRC, XML, титули, реквізити з sample, українська мова,
непорожні розділи, відповідність основних чисел і коду. Реквізити не змінювалися.
Висновки переформульовано безособово; застарілі твердження про відсутній GitHub/CI оновлено.
DOCX здаються окремо; [перелік](SUBMISSION.md). Точну пагінацію Microsoft Word не підтверджено:
Відтворення сторінок у Microsoft Word недоступне: COM 0x80070520. Попередні браузерні прев'ю є в окремому комплекті.

Docker build/run, public deployment, deployed oha та install-from-GitHub-Release не виконані.
Виправлений Dockerfile звірено за файлами/командами, але це не виконання контейнера.
Релізні wheel і описи підготовлено локально, Releases відсутні на момент перевірки API.
Ручна незалежна перевірка qrels відсутня. У початковому crawl-log є asyncio startup warning;
це явно збережено у [витягу](evidence/historical/lab06_crawl_excerpt.log), тому твердження
«усі debug-запуски чисті» не робиться. Докладна матриця всіх вимог — [SUBMISSION](SUBMISSION.md).

## Повторна перевірка виправленого main

До чистого клону b02d1be застосовано актуальні src/scripts/tests без копіювання початкових data.
Після виправлення блокуючої ініціалізації AsyncClient та шляхів нових вимірювань:
**104 passed, line coverage 86.573%**. Пройдено Ruff check/format, Pyright strict, Mypy strict,
benchmark comparison і wheel/sdist build. [Exit codes](evidence/submission-2026-11-11/candidate-checks.json),
[pytest log](evidence/submission-2026-11-11/candidate-pytest.log),
[JUnit](evidence/submission-2026-11-11/candidate-junit.xml),
[coverage](evidence/submission-2026-11-11/candidate-coverage.json).

Виконано справжній `findex embed` (3642 чанки, 384 виміри на тому самому корпусі),
CLI keyword/semantic/hybrid, а також 11 HTTP-перевірок: UI, OpenAPI, health/stats,
document, 404, 422 і три режими пошуку. [HTTP results](evidence/submission-2026-11-11/candidate-http.json),
[embed](evidence/submission-2026-11-11/candidate-embed.log).
Новий crawl на власному дзеркалі з concurrency=5 зібрав 200 сторінок, обробив 429 retry,
не містив asyncio `Executing <Task` warning; JSONL успішно індексовано.
[Debug log](evidence/submission-2026-11-11/candidate-crawl-debug.log).
Це контроль виправлення, а не повторення повної таблиці concurrency=1/5/20;
початкові числа продуктивності не змінювалися.

У скриптах нові вимірювання зберігаються в ignored `data/measurements/` замість відсутнього
після clone `../Tests/`; виконано evaluate, sanity_corpus та measure_lab02 з новим шляхом.
Зафіксовані qrels стосуються історичного SHA корпусу; для іншого corpus потрібна нова перевірка відповідності ID.

Повторно виконано історичні suites саме з Git archive кожного тега, з PYTHONPATH=tag/src
і однаковими поточними залежностями. [Tag test results](evidence/submission-2026-11-11/tag-checks.json):
lab-01 — 11, lab-02 — 27, lab-03 — 51, lab-04 — 58, lab-05 — 63,
lab-06 — 74, lab-07 — 85, lab-08 — 103; усі passed. Це різні snapshots, їх не можна додавати до числа 104.
Для lab-08 модель надано окремо з перевіреного offline kit, як і для чистого клону.

Для версій 0.4.0 і 1.0.0 зібрано wheel/sdist з оновленою документацією відповідних
гілок text-review. Python-файли wheel побайтово збігаються з кодом історичного тегу.
Точний source ref і контрольні суми зазначено в маніфестах. [v0.4.0 manifest](evidence/release-v0.4.0-manifest.json),
[v1.0.0 manifest](evidence/release-v1.0.0-manifest.json). Це локальна перевірка пакетів, не публікація Release.
Оновлені DOCX: [CRC/XML/таблиці/код](evidence/reports-validation.json); файли залишаються поза Git.

## Перевірка текстів і оформлення

Для всіх восьми робіт збережено код і числові значення таблиць. У DOCX перевірено незмінність
титулів, стилів, таблиць, формул, скріншотів, колонтитулів і початкових фрагментів коду.
Усі 8 документів відкрито в docx-preview: зображення завантажились, помилок відображення немає.
Перевірено 209 локальних посилань. [Результат перевірки](evidence/editorial-validation.json).
Точну пагінацію Microsoft Word цим переглядом не перевірено.
