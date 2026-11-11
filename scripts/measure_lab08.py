import json
import statistics
import time
from pathlib import Path

from findex.retrieval import retrieve
from findex.scoring import BM25, TfIdf
from findex.search import candidate_ids, search
from findex.store import load
from findex.tokenize import tokenize
from findex.vector import search_numpy, vector_index


def median_ms(function):
    function()
    runs = []
    for _ in range(100):
        start = time.perf_counter_ns()
        function()
        runs.append((time.perf_counter_ns() - start) / 1e6)
    return statistics.median(runs)


def main():
    Path("data/measurements").mkdir(parents=True, exist_ok=True)
    index = load(Path("data/index.npz"))
    scalar_index = load(Path("data/index.bin"))
    vector_index(index)
    rows = []
    for scorer in ["bm25", "tfidf"]:
        for query in ["the", "zscore", "the file return"]:
            reference = search(
                scalar_index,
                query,
                scorer=BM25() if scorer == "bm25" else TfIdf(),
                with_snippets=False,
            )
            actual = search_numpy(index, query, scorer=scorer, with_snippets=False)
            assert [r.doc_id for r in reference] == [r.doc_id for r in actual]
            python_ms = median_ms(
                lambda query=query, scorer=scorer: search(
                    scalar_index,
                    query,
                    scorer=BM25() if scorer == "bm25" else TfIdf(),
                    with_snippets=False,
                )
            )
            numpy_ms = median_ms(
                lambda query=query, scorer=scorer: search_numpy(
                    index, query, scorer=scorer, with_snippets=False
                )
            )
            rows.append(
                {
                    "scorer": scorer,
                    "query": query,
                    "matched": len(candidate_ids(index, query)),
                    "python_ms": python_ms,
                    "numpy_ms": numpy_ms,
                    "speedup": python_ms / numpy_ms,
                }
            )
    Path("data/measurements/lab08_speed.json").write_text(json.dumps(rows, indent=2))
    labels = json.loads(Path("evaluation/qrels.json").read_text(encoding="utf-8"))["queries"]
    paraphrases = [
        ("memoization", [1010], "Збереження результатів повторного обчислення"),
        ("decompression", [1040, 1041], "Розпакування стисненого вмісту"),
        ("checksum", [1044], "Контрольна сума"),
        ("deserialization", [1352, 1353], "Перетворення текстового представлення в об’єкт"),
        ("FIFO", [1785, 1786, 1790, 1791], "Черга: першим прийшов — першим вийшов"),
    ]
    for query, ids, intent in paraphrases:
        overlap = {
            i: sorted(set(tokenize(query)) & set(tokenize(index.doc_meta[i].text))) for i in ids
        }
        # Фіксуємо реальне перекриття, а не стверджуємо нуль, якщо є буквальний збіг.
        labels.append(
            {
                "query": query,
                "relevant": ids,
                "intent": intent,
                "paraphrase": True,
                "overlap": overlap,
            }
        )
    Path("evaluation/qrels_15.json").write_text(
        json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    evaluation = []
    for query in labels:
        row = {**query}
        for mode in ["keyword", "semantic", "hybrid"]:
            started = time.perf_counter()
            results = retrieve(index, query["query"], mode=mode, k=5)
            row[mode] = {
                "p_at_5": sum(r.doc_id in query["relevant"] for r in results) / 5,
                "ids": [r.doc_id for r in results],
                "elapsed_s": time.perf_counter() - started,
            }
        evaluation.append(row)
        Path("data/measurements/lab08_precision.json").write_text(
            json.dumps(evaluation, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            query["query"],
            [row[m]["p_at_5"] for m in ["keyword", "semantic", "hybrid"]],
            flush=True,
        )


if __name__ == "__main__":
    main()
