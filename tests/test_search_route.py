from fastapi.testclient import TestClient
from src.main import app


def test_search_endpoint(monkeypatch):
    client = TestClient(app)

    class DummyIndexer:
        def search_index(self, query: str):  # pragma: no cover - stub
            return ["result"]

    monkeypatch.setattr(
        "src.services.index_service.indexer_rs", DummyIndexer()
    )

    response = client.get("/api/projects/1/search", params={"q": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == 1
    assert data["query"] == "test"
    assert data["hits"] == ["result"]
