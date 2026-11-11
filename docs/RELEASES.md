# Пакети GitHub Release

Методичка №4 прямо вимагає GitHub Release v0.4.0 з wheel та перевірку встановлення
за його URL. У №7 потрібна версія 0.7.0, у №8 — теги lab-08/v1.0.0 і deployed version;
окремий Release для них не зазначений. Тег та Release є різними об'єктами GitHub.

API Releases повернув порожній список під час аудиту 11.11.2026:
[зафіксований стан](evidence/github-before.json). Дозвіл на публікацію коду вже є,
але конектор не має операцій створення Release/завантаження binary asset,
а gh із sandbox не має мережевих сокетів. Пакети підготовлено для звичайної Windows-сесії.

| Пакет | Source | Готовий опис | Перевірка |
|---|---|---|---|
| v0.4.0, обов'язковий №4 | незмінний lab-04 / e70bf890 | [текст](releases/v0.4.0.md) | [SHA256 і побайтова звірка wheel/source](evidence/release-v0.4.0-manifest.json) |
| v1.0.0, додатковий | незмінний lab-08 / b02d1be2 | [текст](releases/v1.0.0.md) | [SHA256 і звірка](evidence/release-v1.0.0-manifest.json) |

Локальне розміщення поза публічним Git: `READY_TO_SUBMIT/Documentation/Releases/Submission/v0.4.0/`
і `.../v1.0.0/`. Кожна папка містить wheel, sdist та SHA256SUMS.txt; тексти опису скопійовано поруч.
У Git не додаються dist, середовища або великі моделі.

Публікація готового №4 через авторизований GitHub CLI зі звичайного термінала
в папці `lab_python/READY_TO_SUBMIT/Project` (конкретний тег уже існує, `--verify-tag` забороняє створити інший):

```powershell
gh release create v0.4.0 --repo editlikeorigin-afk/findex-python-labs --verify-tag --title "findex v0.4.0" --notes-file docs/releases/v0.4.0.md ../Documentation/Releases/Submission/v0.4.0/findex-0.4.0-py3-none-any.whl ../Documentation/Releases/Submission/v0.4.0/findex-0.4.0.tar.gz ../Documentation/Releases/Submission/v0.4.0/SHA256SUMS.txt
```

Якщо `gh` не встановлено, в локальному комплекті використовується
`../../GitHub_Publish/gh/bin/gh.exe` (PowerShell: `&` перед цим шляхом) або офіційний GitHub CLI.
Повторний `release create` для наявного Release завершується помилкою, не перезаписує його.
Перед повторною спробою потрібно перевірити фактичний стан через `gh release view v0.4.0 --repo editlikeorigin-afk/findex-python-labs`.

Лише після успішної публікації перевірити з нового середовища:

```powershell
uv tool install https://github.com/editlikeorigin-afk/findex-python-labs/releases/download/v0.4.0/findex-0.4.0-py3-none-any.whl
findex --help
```

Це **запланований URL після створення Release**, а не вже доступне посилання для здачі.
Встановлення за ним ще не виконувалось. Передавати цей URL як робочий можна тільки після перевірки.
