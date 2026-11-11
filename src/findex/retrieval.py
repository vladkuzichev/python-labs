from pathlib import Path
from typing import Literal

from findex.boolean import Engine
from findex.index import Index
from findex.scoring import BM25, TfIdf
from findex.search import SearchResult, search
from findex.vector import ScorerName, search_numpy

SearchMode = Literal["keyword", "semantic", "hybrid"]
Backend = Literal["python", "numpy"]


def retrieve(
    index: Index,
    query: str,
    *,
    k: int = 10,
    scorer: ScorerName = "bm25",
    mode: SearchMode = "keyword",
    backend: Backend = "numpy",
    engine: Engine = "merge",
    embeddings_path: Path = Path("data/embeddings"),
    model_path: Path = Path("models/all-MiniLM-L6-v2"),
) -> list[SearchResult]:
    if mode == "semantic":
        from findex.semantic import get_semantic

        return get_semantic(index, embeddings_path, model_path).search(query, k)
    count = index.num_docs if mode == "hybrid" else k
    keyword = (
        search_numpy(index, query, k=count, scorer=scorer, engine=engine)
        if backend == "numpy"
        else search(
            index, query, k=count, scorer=BM25() if scorer == "bm25" else TfIdf(), engine=engine
        )
    )
    if mode == "keyword":
        return keyword
    from findex.semantic import get_semantic, reciprocal_rank_fusion

    semantic = get_semantic(index, embeddings_path, model_path).search(query, index.num_docs)
    return reciprocal_rank_fusion([keyword, semantic], k=k)
