# tests/test_search.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_search_graph_returns_results():
    # Avec le seed, "graph" est présent dans les titres/tags
    response = client.get("/api/search", params={"q": "graph"})
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "graph"
    assert isinstance(data["results"], list)
    # On s'attend à au moins un article avec "graph" quelque part
    assert len(data["results"]) >= 1

    first = data["results"][0]
    assert "id" in first
    assert "title" in first
    # topics & tags doivent exister dans le schema
    assert "topics" in first
    assert "tags" in first
