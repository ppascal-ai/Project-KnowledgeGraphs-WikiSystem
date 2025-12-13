# tests/test_articles.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_related_articles_for_article_1():
    # Avec le seed, article-1 est lié à article-2 et article-3
    response = client.get("/api/articles/article-1/related")
    assert response.status_code == 200

    data = response.json()
    assert data["article_id"] == "article-1"
    assert isinstance(data["related"], list)

    # On s'attend à au moins un article lié
    assert len(data["related"]) >= 1

    first = data["related"][0]
    assert "article" in first
    assert "score" in first

    article = first["article"]
    assert "id" in article
    assert "title" in article
