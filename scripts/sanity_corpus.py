"""Три перевірки ранжування з реальними документами повного корпусу."""

import json
from pathlib import Path

from findex.index import Posting
from findex.scoring import BM25, TfIdf
from findex.search import search
from findex.store import load


def main():
    index = load(Path("data/index.bin"))
    rows = []
    rare = "zscore"
    common = "the"
    for name, scorer in [("bm25", BM25()), ("tfidf", TfIdf())]:
        result = search(
            index, f"{rare} OR {common}", scorer=scorer, k=index.num_docs, with_snippets=False
        )
        rare_ids = {p.doc_id for p in index[rare]}
        best_rare = next(r for r in result if r.doc_id in rare_ids)
        best_common = next(r for r in result if r.doc_id not in rare_ids)
        assert best_rare.score > best_common.score
        rows.append(
            {
                "check": "rare_vs_common",
                "scorer": name,
                "rare": rare,
                "common": common,
                "rare_doc": best_rare.doc_id,
                "rare_title": best_rare.title,
                "rare_score": best_rare.score,
                "common_doc": best_common.doc_id,
                "common_title": best_common.title,
                "common_score": best_common.score,
            }
        )
    repeated = next(p for p in index[common] if p.tf >= 20)
    scores = {
        str(tf): BM25().score(common, Posting(repeated.doc_id, tf), index) for tf in [1, 2, 19, 20]
    }
    first = scores["2"] - scores["1"]
    last = scores["20"] - scores["19"]
    assert last < first
    rows.append(
        {
            "check": "saturation",
            "doc_id": repeated.doc_id,
            "title": index.doc_meta[repeated.doc_id].title,
            "term": common,
            "actual_tf": repeated.tf,
            "fixed_doc_length": index.doc_length(repeated.doc_id),
            "scores": scores,
            "gain_2": first,
            "gain_20": last,
            "method": (
                "Controlled scorer calculation: real document/IDF/length; "
                "only observed TF is capped at n occurrences."
            ),
        }
    )
    ones = [p for p in index["return"] if p.tf == 1]
    short = min(ones, key=lambda p: index.doc_length(p.doc_id))
    long = max(ones, key=lambda p: index.doc_length(p.doc_id))
    short_score = BM25().score("return", short, index)
    long_score = BM25().score("return", long, index)
    assert short_score > long_score
    rows.append(
        {
            "check": "length",
            "term": "return",
            "short_doc": short.doc_id,
            "short_length": index.doc_length(short.doc_id),
            "short_score": short_score,
            "long_doc": long.doc_id,
            "long_length": index.doc_length(long.doc_id),
            "long_score": long_score,
        }
    )
    Path("../Tests/lab03_sanity_corpus.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
