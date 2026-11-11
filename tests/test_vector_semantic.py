import numpy as np
import pytest

from findex.scoring import BM25, TfIdf
from findex.search import SearchResult, search
from findex.semantic import MiniLM, SemanticIndex, embed, reciprocal_rank_fusion
from findex.store import load, save, to_dict
from findex.vector import search_numpy, top_k, vector_index


@pytest.mark.parametrize(
    "query", ["python", "event loop", "python OR java", "NOT thread", '"event loop"']
)
@pytest.mark.parametrize("scorer", ["bm25", "tfidf"])
def test_identical_ranking(index, query, scorer):
    expected = search(index, query, scorer=BM25() if scorer == "bm25" else TfIdf())
    actual = search_numpy(index, query, scorer=scorer)
    assert [r.doc_id for r in actual] == [r.doc_id for r in expected]
    np.testing.assert_allclose(
        [r.score for r in actual], [r.score for r in expected], rtol=1e-12, atol=1e-12
    )


def test_arrays(index):
    view = vector_index(index)
    assert view.doc_len.dtype == np.int32
    assert all(
        p.doc_ids.dtype == np.int32 and p.tfs.dtype == np.int32 for p in view.postings.values()
    )


def test_numpy_roundtrip(index, tmp_path):
    path = tmp_path / "index.npz"
    save(index, path)
    restored = load(path)
    assert to_dict(restored) == to_dict(index)
    assert search_numpy(restored, "python") == search_numpy(index, "python")


def test_topk_ties():
    ids = np.asarray([3, 2, 1, 0], dtype=np.int32)
    values = np.ones(4, dtype=np.float64)
    assert ids[top_k(ids, values, 2)].tolist() == [0, 1]


def test_rrf():
    a = SearchResult(0, 100, "a")
    b = SearchResult(1, 0.1, "b")
    result = reciprocal_rank_fusion([[a, b], [b]], k=2)
    assert result[0].doc_id == 1
    assert result[0].score == pytest.approx(1 / 62 + 1 / 61)


@pytest.fixture(scope="module")
def model():
    from pathlib import Path

    return MiniLM(Path("models/all-MiniLM-L6-v2"))


@pytest.mark.slow
def test_real_embeddings(model):
    embeddings = model.encode(
        ["the cat sat on the mat", "a feline rested on the rug", "the stock market fell"]
    )
    assert embeddings.shape == (3, 384)
    np.testing.assert_allclose(np.linalg.norm(embeddings, axis=1), 1, atol=1e-5)
    cosine = embeddings @ embeddings.T
    assert cosine[0, 1] > cosine[0, 2] + 0.15


@pytest.mark.slow
def test_embedding_store(index, model, tmp_path):
    metadata = embed(index, model, tmp_path)
    assert metadata["documents"] == 4
    semantic = SemanticIndex(index, tmp_path, model)
    result = semantic.search("asynchronous event loop", 2)
    assert len(result) == 2 and result[0].doc_id == 0
