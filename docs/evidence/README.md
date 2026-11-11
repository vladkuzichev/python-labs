# Походження доказів

- `github-before.json`, `github-actions-known.json` — фактичні відповіді/резюме GitHub API під час перевірки;
  green run стосується конкретного b02d1be, а не автоматично всіх майбутніх комітів.
- `methods-check.json` — Git blob SHA локальних методичок та notes звірено з GitHub викладача.
- `tag-audit.json` — список файлів незмінних тегів, отриманий локальним git ls-tree;
  їхні SHA також перевірено через GitHub API.
- `historical/` — вибрані справжні журнали попередніх дослідів; повні первинні логи —
  `READY_TO_SUBMIT/Tests/` окремого комплекту. Витяг crawler навмисно зберігає старе startup warning.
- `submission-2026-11-11/` — новий clean-clone дослід і наступний candidate overlay з виправленнями.
  `checks.json` містить також невдалі offline sync; `candidate-checks.json` — повтор після виправлень.
  Ці timings не підміняють вихідні таблиці продуктивності.
- `release-v*.json` — source SHA, hash локальних пакетів та звірка Python-файлів wheel із тегом.
  Це не доказ опублікованого GitHub Release.
- `reports-validation.json` — CRC/XML, незмінність титулу/таблиць та збіг фрагментів DOCX з кодом;
  самі звіти й реквізити не публікуються. Переноси сторінок у Microsoft Word потребують ручного перегляду.
- `scalene-index-audit-summary.json` — додаткове вимірювання, окреме від профілю до оптимізації.

Абсолютний шлях робочої папки у нових текстових доказах може бути замінено позначкою `<lab_python>`.
Ця нормалізація не змінює числових результатів, exit codes або змісту оброблених помилок.
