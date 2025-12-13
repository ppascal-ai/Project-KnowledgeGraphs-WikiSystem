# tests/test_authors.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_author_contributions_author_1():
    # Dans le seed, author-1 existe
    response = client.get("/api/authors/author-1/contributions")
    assert response.status_code == 200

    data = response.json()
    author = data["author"]

    assert author["id"] == "author-1"
    assert "name" in author

    # Il doit avoir écrit au moins un article dans le seed
    assert isinstance(data["articles"], list)
    assert len(data["articles"]) >= 1

    # Et des topics/tags associés
    assert isinstance(data["topics"], list)
    assert isinstance(data["tags"], list)
