# Захист лабораторної №8

## Команди

```powershell
uv sync --frozen
uv run python scripts/prepare_corpus.py
uv run findex index data/stdlib.jsonl --positions --out data/index.npz
uv run python scripts/download_model.py
uv run findex embed data/index.npz --out data/embeddings
uv run findex search data/index.npz memoization --mode semantic
uv run findex search data/index.npz decompression --mode hybrid
```

## Reflection

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
