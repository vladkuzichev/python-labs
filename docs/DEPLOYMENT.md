# Підготовка розгортання

Стан 11.11.2026: код публічний, FastAPI доступний локально після запуску.
Публічний URL сервісу, cloud deployment та oha-рядок deployed відсутні.
Docker під час перевірки не встановлено, тому наведені контейнерні команди ще не виконано.
Цей документ і render.yaml не є доказом виконаного розгортання.

## Що виправлено

Колишній Dockerfile копіював `data/index.npz`, ембеддинги та модель з робочої папки,
але ці каталоги ігноруються Git. Тепер builder встановлює locked dependencies, запускає
`scripts/prepare_corpus.py` та `findex index` усередині образу. Runtime — окремий slim-stage,
користувач `findex` має UID 10001, індекс завантажується зі змінних оточення.
`WITH_SEMANTIC=1` додатково завантажує зафіксовану модель і створює ембеддинги.
Для keyword-only образу додаткова модель не потрібна.

## Команди для машини з Docker

З кореня клону; build потребує інтернету для базових образів, uv/PyPI, а semantic build — також Hugging Face:

```powershell
docker build -t findex:submission .
docker run --rm -p 8000:8000 -e INDEX_PATH=/app/data/index.npz findex:submission
```

Альтернативне складання з семантичними ресурсами:

```powershell
docker build --build-arg WITH_SEMANTIC=1 -t findex:semantic .
docker run --rm -p 8000:8000 findex:semantic
```

З іншого термінала перевірити `http://127.0.0.1:8000/health`, `/stats`, `/search?q=python`, UI та `/docs`.
Контейнерний HEALTHCHECK використовує порт 8000. CLI слухає `0.0.0.0:8000`, а не loopback контейнера.

## Підготовка Render

[render.yaml](../render.yaml) описує Docker web service, `/health` та INDEX_PATH/MODEL_PATH/EMBEDDINGS_PATH.
Параметр середовища WITH_SEMANTIC=1 передається Render також як build argument відповідно до
[офіційної документації](https://render.com/docs/docker#environment-variable-translation).
Поля Docker Blueprint звірено з [довідкою Render](https://render.com/docs/blueprint-spec#docker).

Для фактичного розгортання потрібні обліковий запис хостингу, вибір сервісу/ресурсів та його створення.
Для розгортання потрібен налаштований обліковий запис Render і вибраний тариф.
Після вибору доступного хостингу можна створити Blueprint з цього репозиторію, перевірити build log,
startup log, health check, keyword і semantic/hybrid, потім додати отриманий реальний URL до README.
Наявний тег v1.0.0 не переміщується: виправлення контейнера знаходиться у наступному коміті main.
Для deployment слід зафіксувати SHA цього виправленого коміту; API-версія залишається 1.0.0.

## Чого бракує для №7–8

Потрібні підтверджений build/run Docker, доступний сторонньому користувачу URL,
успішний `/health`, журнали платформи та реальне вимірювання `oha` з concurrency=20.
Приклад після отримання URL (підставити фактичну адресу замість `<PUBLIC_URL>`):

```text
oha --json -n 1000 -c 20 "<PUBLIC_URL>/search?q=python"
```

Вихід потрібно зберегти з датою, SHA deployment, параметрами інстансу та версією oha,
додати рядок deployed з RPS/p50/p95/p99 до вимірювань. Локальні числа не переносяться в цей рядок.
