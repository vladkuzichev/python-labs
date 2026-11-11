# Захист лабораторних 1–8

Команди демонстрації та відповіді на Reflection.
Посилання на всі оригінальні завдання й notes: [SUBMISSION](SUBMISSION.md).

## Підготовка демонстрації

Команди виконуються з кореня клону після `uv sync --frozen`:

```powershell
uv run --frozen python scripts/prepare_corpus.py
uv run --frozen findex index data/stdlib.jsonl --positions --out data/index.npz
uv run --frozen findex index data/stdlib.jsonl --positions --out data/index.bin
uv run --frozen python scripts/download_model.py
uv run --frozen findex embed data/index.npz --out data/embeddings
```

Інтернет потрібен для першого встановлення залежностей і завантаження MiniLM.
Перед демонстрацією корпусу потрібно звірити SHA з попереднім маніфестом; за іншої версії
Python конкретні doc_id та старі qrels можуть не відповідати новим документам.

## П'ятихвилинний показ

1. 0:00–0:45: генератор, NFC, lazy/eager; відкрити таблицю №1 у README.
2. 0:45–1:30: phrase/OR/NOT, порівняння скорерів, заголовок і snippet.
3. 1:30–2:15: таблиця та графік потоків/процесів, пояснення накладу spawn і merge.
4. 2:15–3:00: локальний краулер, оброблений 429, індексація JSONL.
5. 3:00–4:00: вебформа, `/docs`, `/health`, semantic/hybrid; публічний URL поки відсутній.
6. 4:00–5:00: flame graph, common/rare NumPy, 15-query P@5 та один справжній баг.

Для окремого захисту обирається демонстрація відповідного етапу й 2–3 питання нижче.
У №7–8 вимога саме публічної демонстрації залишається відкритою; localhost її не замінює.

## Короткі команди за етапами

```powershell
# 01: однакові статистики, різні пік пам'яті та час
uv run --frozen python -m findex.stats data/stdlib.jsonl --limit 100
uv run --frozen python -m findex.stats data/stdlib.jsonl --limit 100 --eager
# 02: збереження й пошук із файла
uv run --frozen python -m findex.index data/stdlib.jsonl --positions --out data/index.bin
uv run --frozen python -m findex.search data/index.bin 'python OR asyncio'
# 03: той самий запит двічі в одному процесі для cache hit
uv run --frozen python scripts/evaluate.py
# 04: перевірки CLI, помилка очікуваного вводу, пакування
uv run --frozen findex search data/index.npz 'python OR asyncio' --json
uv run --frozen findex search data/missing.npz python
uv build
# 05: три executor на однаковому зрізі; таблиця повного досліду вже в README
uv run --frozen findex -v index data/stdlib.jsonl --limit 100 --positions --executor serial --workers 1 --out data/serial.npz
uv run --frozen findex -v index data/stdlib.jsonl --limit 100 --positions --executor threads --workers 2 --out data/threads.npz
uv run --frozen findex -v index data/stdlib.jsonl --limit 100 --positions --executor processes --workers 2 --out data/processes.npz
# 07–08: сервер, semantic та hybrid
uv run --frozen findex search data/index.npz memoization --mode semantic --k 5
uv run --frozen findex search data/index.npz decompression --mode hybrid --k 5
uv run --frozen findex serve --port 8010
```

`data/missing.npz` навмисно відсутній: очікується ненульовий код без traceback.
`evaluate.py` використовує зафіксовану розмітку релевантності; вихід не є незалежною людською оцінкою.
Демонстрація №6 — два термінали: `uv run --frozen uvicorn scripts.mirror:app --port 8766`,
потім `uv run --frozen findex crawl http://127.0.0.1:8766/ --max-pages 200 --concurrency 5 --out data/crawl.jsonl`
і `uv run --frozen findex index data/crawl.jsonl --out data/crawled.npz`.

## Lab 01

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

## Lab 02

1. Hash задає початкову позицію у таблиці; при колізії CPython пробує інші слоти за своєю
   послідовністю probing і перевіряє рівність ключів. Це не зовнішній зв'язний список.
2. Потрібно `a == b ⇒ hash(a) == hash(b)` і незмінність hash, поки ключ у dict.
   Якщо hash залежить від mutable поля і поле змінити, lookup може шукати не в тому слоті.
3. List mutable, тому не має hash. Tuple хешується тільки якщо хешуються всі елементи;
   `(1, [2])` містить unhashable list і теж не хешується.
4. Frozen dataclass за звичайних параметрів eq генерує hash із полів. Власний `__eq__`
   без узгодженого `__hash__` зазвичай робить клас unhashable.
5. Plain instance має наклад заголовка й сховища атрибутів; точні байти залежать від CPython.
   Slots задає фіксовані поля; довільні нові атрибути не підтримуються без явного `__dict__`.
6. List зберігає покажчики, а Python int є окремим об'єктом; `array('I')` зберігає самі
   числа (`itemsize` перевіряється на платформі). Дві 32-бітні колонки — 8 байтів на пару без контейнерного накладу.
7. Merge — O(n+m) часу та впорядкований вихід; set має середній O(n+m) на побудову/операцію
   і додаткову пам'ять. У вимірюванні set виграв на частих термінах, merge — на рідких.
8. Pickle описує відновлення Python-об'єктів і може викликати функції під час load.
   Тому чужий файл може виконати довільний код; JSON/NPZ без pickle не мають цього механізму.

## Lab 03

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

## Lab 04

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

## Lab 05

1. GIL у звичайному CPython обмежує одночасне виконання Python-коду в одному інтерпретаторі
   й захищає його внутрішні структури. Він не забезпечує атомарність бізнес-операцій або відсутність гонок.
2. CPU-потоки чергуються за GIL, додають scheduling і синхронізацію; це не вісім незалежних Python-ядер.
   Частина I/O та native extension може виконуватись без GIL.
3. У прикладі питання 8 s wall / 45 s CPU — сумарна робота кількох процесів за ті самі 8 секунд.
   Це навчальний приклад, не число з таблиці findex; в нашому досліді процеси не виграли.
4. Функція має імпортуватися воркером за модулем та ім'ям для pickle/spawn.
   Lambda/локальна функція звичайним pickle не передається.
5. Spawn стартує свіжий Python і імпортує модуль; потрібен guard від повторного запуску pool.
   Fork копіює стан процесу, включно з проблемними locks багатопотокового батька; його доступність залежить від ОС.
6. Амдал: `S(N)=1/(s+(1-s)/N)`. За послідовної частки 15% верхня межа — 1/0.15≈6.67×.
   У findex послідовними лишаються підготовка JSONL-частин і merge.
7. Free-threading прибирає GIL і може проявити справжні гонки спільного стану. У цьому
   проєкті воркери будують незалежні індекси; гонку не спостерігали й не вигадували.
8. Read-modify-write логічно має читання, додавання, запис. Конкретний dis і можливі
   точки перемикання залежать від версії; один запуск із правильним числом не доводить thread safety.
9. Threads — блокуючий I/O; processes — достатньо великі CPU-задачі Python;
   asyncio — багато очікувань async I/O. Для дуже дрібних задач найкращим може бути serial.

## Lab 06

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

## Lab 07

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

## Lab 08

1. cProfile інструментує виклики, py-spy семплує стек зовнішнього процесу,
   Scalene розділяє Python/native/system. Для low-overhead attach зручний py-spy за наявності прав ОС.
2. Python scalar addition виконує динамічний dispatch і працює з об'єктами; NumPy ufunc
   обробляє суцільний typed buffer у native loop, іноді SIMD. 100× — можливий приклад, не обіцянка.
3. `(N,1)` та `(1,M)` broadcast до `(N,M)`. Входи не потребують матеріалізації розтягнутих
   копій, але звичайний результат займає N×M×itemsize байтів, якщо немає спеціального out/іншого алгоритму.
4. Argpartition виділяє top-k приблизно за лінійний час без повного упорядкування всіх N.
   Вибрані k потім сортуються; argsort упорядковує всі N за O(N log N).
5. Великі postings амортизують наклад NumPy, короткі — ні. Тут фактично BM25/the дав
   9.46×, а zscore 0.38×; числа 40×/1.5× у питанні є прикладом, не результатом findex.
6. Embedding — числове подання змісту. Cosine дорівнює dot product поділеному на норми;
   для L2-нормованих векторів знаменник 1, тому використовується `E @ q`.
7. Довгий документ може обрізатися моделлю або змішувати теми. Чанки зберігають локальний
   зміст, а best chunk per document не дає довгому документу зайняти весь top-k своїми шматками.
8. RRF додає `1/(60+rank)` для кожного рейтингу. Ранги порівнювані, сирі BM25 і cosine
   мають різні шкали; пряме додавання створює довільну перевагу одного скорера.
9. На парафразах keyword не знаходив буквального збігу; semantic допоміг лише частині,
   а hybrid не став універсальним переможцем. Середні all15: 0.147/0.133/0.147;
   неповна розмітка релевантності не дають підстав для незалежного висновку про якість.
10. 50 млн × 384 × 4 байти — приблизно 76.8 ГБ лише float32-векторів, плюс metadata.
    Лінійний scan і RAM стають вузькими місцями; потрібні виміряні ANN/HNSW/FAISS,
    шардінг чи стиснення з перевіркою recall, а не необґрунтована заміна всього проєкту.

## Справжній баг для обговорення

У початковому crawl-log зафіксовано asyncio warning: конструювання AsyncClient синхронно
ініціалізувало SSL-контекст. В main ініціалізацію перенесено в `asyncio.to_thread`;
регресійний тест затримує constructor й перевіряє, що loop продовжує виконувати інші задачі.
Старі вимірювання не переписано; новий debug-дослід збережено окремо у [VALIDATION](VALIDATION.md).
Інший попередній баг: Typer 0.16 не приймав Literal як CLI-тип; на межі CLI використано Enum,
а Literal залишено у внутрішньому API. Тести запускають справжній CliRunner.
