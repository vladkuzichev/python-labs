import pytest
from fastapi.testclient import TestClient

from findex.web.app import create_app, get_index
from findex.web.settings import Settings


@pytest.fixture
def client(index):
    app = create_app(Settings(index_path="missing-test-index.bin"))
    app.dependency_overrides[get_index] = lambda: index
    with TestClient(app) as client:
        yield client


def test_search(client):
    response = client.get("/search", params={"q": "python", "k": 1})
    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 2 and len(result["results"]) == 1
    second = client.get("/search", params={"q": "python", "k": 1, "page": 2}).json()
    assert second["results"][0]["doc_id"] != result["results"][0]["doc_id"]


@pytest.mark.parametrize(
    "params",
    [
        {"q": ""},
        {"q": "a", "k": 0},
        {"q": "a", "page": 0},
        {"q": "a", "scorer": "bad"},
        {"q": "a", "k": 101},
    ],
)
def test_validation(client, params):
    assert client.get("/search", params=params).status_code == 422


def test_document(client):
    assert client.get("/docs/0").json()["doc_id"] == 0
    assert client.get("/docs/9999").status_code == 404
    assert client.get("/doc/0").status_code == 200
    assert client.get("/doc/9999").status_code == 404


def test_health_stats_ui(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/stats").json()["documents"] == 4
    assert "<mark>" in client.get("/", params={"q": "python"}).text
    assert client.get("/docs").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_unloaded():
    with TestClient(create_app(Settings(index_path="missing-test-index.bin"))) as client:
        assert client.get("/health").status_code == 503


def test_query_error(client):
    assert client.get("/search", params={"q": "a OR"}).status_code == 400


def test_clean_500():
    def broken():
        raise RuntimeError("sensitive stack details")

    app = create_app(Settings(index_path="missing.bin"))
    app.dependency_overrides[get_index] = broken
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/search", params={"q": "python"})
        assert response.status_code == 500
        assert "sensitive" not in response.text
        assert response.json()["request_id"] == response.headers["X-Request-ID"]
