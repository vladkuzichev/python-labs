import logging

import pytest

from findex.corpus import Document
from findex.index import build_index
from findex.query import And, Not, Or, Phrase, Term, parse
from findex.scoring import BM25, TfIdf
from findex.search import candidate_ids, search, snippet
from findex.store import open_index, save


@pytest.mark.parametrize(
    "query,tree",
    [
        ("a OR b c", Or(Term("a"), And(Term("b"), Term("c")))),
        ("a AND (b OR c) NOT d", And(And(Term("a"), Or(Term("b"), Term("c"))), Not(Term("d")))),
        ('"event loop"', Phrase(("event", "loop"))),
        ("NOT NOT a", Not(Not(Term("a")))),
    ],
)
def test_trees(query, tree):
    assert parse(query) == tree


@pytest.mark.parametrize("query", ["", "a OR", "(a", "a)", '"bad', "()", "a AND AND b", '""'])
def test_invalid(query):
    with pytest.raises(ValueError):
        parse(query)


def test_operators():
    a, b = Term("a"), Term("b")
    assert a & ~b == And(a, Not(b))
    assert a | b == Or(a, b)


def test_phrase(index):
    assert parse('"event loop"').evaluate(index) == [0, 2]
    assert parse('"loop event"').evaluate(index) == []


def test_phrase_requires_positions(docs):
    with pytest.raises(ValueError):
        parse('"event loop"').evaluate(build_index(docs))


def test_mapping(index):
    assert len(index) == len(list(index))
    assert "python" in index
    assert index.num_docs == 4
    assert index.avg_doc_length == 2.5
    assert index.df("python") == 2
    assert "documents=4" in repr(index)
    with pytest.raises(KeyError):
        index["missing"]


@pytest.mark.parametrize("scorer", [BM25(), TfIdf()])
def test_rare_outranks_common(scorer):
    docs = [
        Document(0, "a", "rare", "rare"),
        Document(1, "b", "common", "common"),
        Document(2, "c", "common", "filler"),
    ]
    result = search(build_index(docs), "rare OR common", scorer=scorer)
    assert result[0].doc_id == 0


def test_short_beats_long():
    docs = [Document(0, "a", "word", "short"), Document(1, "b", "word " + "noise " * 1000, "long")]
    assert search(build_index(docs), "word")[0].doc_id == 0


def test_bm25_saturation():
    # Відокремлено TF від довжини: усі документи мають 100 токенів.
    docs = [Document(n, "a", "word " * n + "noise " * (100 - n), str(n)) for n in [1, 2, 19, 20]]
    index = build_index(docs)
    scores = {p.doc_id: BM25().score("word", p, index) for p in index["word"]}
    assert scores[20] - scores[19] < (scores[2] - scores[1]) / 20


def test_cache_logging(index, caplog):
    candidate_ids.cache_clear()
    with caplog.at_level(logging.INFO):
        search(index, "python")
        search(index, "python")
    assert "hit=True" in caplog.text


def test_snippet_escapes():
    result = snippet("<script>alert(1)</script> python", ("python",))
    assert "<script>" not in result
    assert "<mark>python</mark>" in result


def test_context_exception(index, tmp_path):
    path = tmp_path / "index.bin"
    save(index, path)
    with pytest.raises(RuntimeError), open_index(path) as opened:
        raise RuntimeError("test")
    assert opened.closed


def test_not_only(index):
    assert [r.doc_id for r in search(index, "NOT python")] == [2, 3]
