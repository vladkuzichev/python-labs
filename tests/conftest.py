import pytest

from findex.corpus import Document
from findex.index import build_index


@pytest.fixture
def docs():
    return [
        Document(0, "a", "Python async event loop", "Async"),
        Document(1, "b", "Python thread thread", "Threads"),
        Document(2, "c", "Java event loop", "Java"),
        Document(3, "d", "", "Empty"),
    ]


@pytest.fixture
def index(docs):
    return build_index(iter(docs), positions=True)
