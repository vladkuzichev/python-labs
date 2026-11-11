import pytest

from findex.index import build_index
from findex.search import search


@pytest.mark.benchmark
def test_benchmark_search(benchmark, index):
    result = benchmark(search, index, "python OR java", k=2)
    assert len(result) == 2


@pytest.mark.benchmark
def test_benchmark_build(benchmark, docs):
    index = benchmark(build_index, docs, positions=True)
    assert index.num_docs == 4
