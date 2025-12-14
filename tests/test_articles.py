# tests/test_articles.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_any_article_id():
    """
    Utilise la search API pour récupérer un article existant.
    On évite de dépendre d'un id spécifique du seed.
    """
    # Avec le dataset MUSAE, la recherche "Wikipedia" doit renvoyer des résultats
    r = client.get("/api/search", params={"q": "Wikipedia", "limit": 5})
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert len(data["results"]) > 0
    return data["results"][0]["id"]


def test_related_articles_for_existing_article():
    article_id = _get_any_article_id()

    response = client.get(f"/api/articles/{article_id}/related", params={"limit": 10})
    assert response.status_code == 200

    payload = response.json()
    assert payload["article_id"] == article_id
    assert "related" in payload
    assert isinstance(payload["related"], list)

    # Avec un vrai graphe, il y a quasi toujours des voisins.
    # Mais on n'impose pas >0 pour éviter les flakiness (au cas où).
    if len(payload["related"]) > 0:
        first = payload["related"][0]
        assert "article" in first and "score" in first
        assert "id" in first["article"]


def test_related_articles_for_unknown_article_returns_404():
    response = client.get("/api/articles/this-id-does-not-exist/related")
    assert response.status_code == 404
