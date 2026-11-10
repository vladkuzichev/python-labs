"""Precision@5 з явно заданими судженнями, без підгонки під отриманий рейтинг."""

import json
import logging
from pathlib import Path

from findex.scoring import BM25, TfIdf
from findex.search import search
from findex.store import load


def main():
    logging.basicConfig(level=logging.INFO)
    index = load(Path("data/index.bin"))
    labels = json.loads(Path("evaluation/qrels.json").read_text(encoding="utf-8"))
    rows = []
    for q in labels["queries"]:
        row = {"query": q["query"], "relevant": q["relevant"]}
        for name, scorer in [("tfidf", TfIdf()), ("bm25", BM25())]:
            results = search(index, q["query"], scorer=scorer, k=5)
            row[name] = {
                "p_at_5": sum(r.doc_id in q["relevant"] for r in results) / 5,
                "ids": [r.doc_id for r in results],
            }
        rows.append(row)
    search(index, "event loop")
    search(index, "event loop")
    Path("../Tests/lab03_precision.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
