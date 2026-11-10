"""Реальні виміри формату, Boolean-операцій та трьох подань постінгів."""

import json
import pickle
import time
import tracemalloc
from array import array
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from findex.boolean import combine
from findex.corpus import iter_documents
from findex.index import Posting, build_index
from findex.store import load, save, to_dict
from findex.tokenize import tokenize


@dataclass(frozen=True)
class PlainPosting:
    doc_id: int
    tf: int
    positions: tuple[int, ...] = ()


def representation(corpus, kind):
    values = {}
    for doc in iter_documents(corpus):
        for term, tf in Counter(tokenize(doc.text)).items():
            if kind == "array":
                if term not in values:
                    values[term] = (array("I"), array("I"))
                values[term][0].append(doc.doc_id)
                values[term][1].append(tf)
            else:
                values.setdefault(term, []).append(
                    PlainPosting(doc.doc_id, tf) if kind == "plain" else Posting(doc.doc_id, tf))
    return values


def main():
    corpus = Path("data/stdlib.jsonl")
    out = Path("../Tests")
    measurements = {"storage": [], "formats": [], "boolean": []}
    for kind in ["plain", "slots", "array"]:
        tracemalloc.start()
        t0 = time.perf_counter()
        values = representation(corpus, kind)
        elapsed = time.perf_counter() - t0
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        payload = pickle.dumps(values, protocol=5)
        t0 = time.perf_counter()
        restored = pickle.loads(payload)
        load_s = time.perf_counter() - t0
        assert len(restored) == len(values)
        measurements["storage"].append(dict(kind=kind, peak_bytes=peak, file_bytes=len(payload),
                                             build_s=elapsed, load_s=load_s))
        del values, payload, restored
    index = build_index(iter_documents(corpus), positions=True)
    for suffix in [".json", ".bin"]:
        path = Path("data/index" + suffix)
        t0 = time.perf_counter()
        save(index, path)
        save_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        restored = load(path)
        load_s = time.perf_counter() - t0
        assert to_dict(restored) == to_dict(index)
        measurements["formats"].append(dict(format=suffix, file_bytes=path.stat().st_size,
                                              save_s=save_s, load_s=load_s))
    counts = sorted(index.postings, key=lambda t: (-len(index.postings[t]), t))
    for label, terms in [("common", counts[:2]), ("rare", counts[-2:])]:
        for engine in ["merge", "set"]:
            a, b = ([p.doc_id for p in index.postings[t]] for t in terms)
            runs = []
            for _ in range(100):
                t0 = time.perf_counter_ns()
                combine(a, b, "AND", engine)
                runs.append((time.perf_counter_ns()-t0)/1e6)
            measurements["boolean"].append(dict(terms=terms, label=label, engine=engine,
                                                 median_ms=median(runs)))
    no_positions = build_index(iter_documents(corpus), positions=False)
    measurements["positions"] = {"enabled_bytes":len(pickle.dumps(to_dict(index))),
                                  "disabled_bytes":len(pickle.dumps(to_dict(no_positions)))}
    (out / "lab02_measurements.json").write_text(json.dumps(measurements, indent=2), encoding="utf-8")
    print(json.dumps(measurements, indent=2))


if __name__ == "__main__":
    main()
