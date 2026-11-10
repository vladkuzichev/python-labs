from pathlib import Path

import pytest

from findex.boolean import difference, intersect, union
from findex.corpus import iter_documents
from findex.index import DocMeta, Posting, build_index
from findex.search import boolean_search
from findex.store import load, save, to_dict


def test_build(index):
    assert index.postings["thread"] == [Posting(1, 2, (1, 2))]
    assert index.doc_lengths == {0: 4, 1: 3, 2: 3, 3: 0}


def test_hashable():
    assert {Posting(0, 1), Posting(0, 1)} == {Posting(0, 1)}
    assert len({DocMeta("p", "t", "x"), DocMeta("p", "t", "x")}) == 1


@pytest.mark.parametrize("a,b", [([], []), ([1], []), ([], [2]), ([1, 3, 7], [3, 5, 7])])
def test_merge(a, b):
    assert intersect(a, b) == sorted(set(a) & set(b))
    assert union(a, b) == sorted(set(a) | set(b))
    assert difference(a, b) == sorted(set(a) - set(b))


@pytest.mark.parametrize("query,expected", [("python", [0, 1]), ("python thread", [1]),
    ("python OR java", [0, 1, 2]), ("python NOT thread", [0]), ("unknown", [])])
def test_boolean(index, query, expected):
    assert boolean_search(index, query) == expected
    assert boolean_search(index, query, engine="set") == expected


@pytest.mark.parametrize("suffix", [".json", ".bin"])
def test_roundtrip(index, tmp_path, suffix):
    path = tmp_path / ("index" + suffix)
    save(index, path)
    assert to_dict(load(path)) == to_dict(index)


def test_duplicate_id(docs):
    with pytest.raises(ValueError):
        build_index([docs[0], docs[0]])


def test_bad_encoding(tmp_path):
    (tmp_path / "bad.txt").write_bytes(b"hello\xffworld")
    assert "hello" in next(iter_documents(tmp_path)).text


def test_missing_corpus():
    with pytest.raises(FileNotFoundError):
        next(iter_documents(Path("definitely-not-a-corpus")))
