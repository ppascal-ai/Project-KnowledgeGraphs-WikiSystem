# app/routers/articles.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Article,
    RelatedArticle,
    RelatedArticlesResponse,
)

router = APIRouter(prefix="/api", tags=["articles"])


def _node_to_article(node) -> Article:
    return Article(
        id=node.get("id"),
        title=node.get("title"),
        summary=node.get("summary"),
        url=node.get("url"),
        source=node.get("source"),
        language=node.get("language"),
    )


@router.get(
    "/articles/{article_id}/related",
    response_model=RelatedArticlesResponse,
)
def get_related_articles(
    article_id: str = Path(..., description="ID of the source article"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Renvoie les articles liés à un article donné via la relation RELATED_ARTICLE.
    """
    # D'abord vérifier que l'article existe
    exists_cypher = "MATCH (a:Article {id: $article_id}) RETURN a LIMIT 1"
    record = db.run(exists_cypher, article_id=article_id).single()
    if record is None:
        raise HTTPException(status_code=404, detail="Article not found.")

    cypher = """
    MATCH (a:Article {id: $article_id})
    OPTIONAL MATCH (a)-[r:RELATED_ARTICLE]->(other:Article)
    RETURN other, r.score AS score
    ORDER BY score DESC
    LIMIT $limit
    """

    records = db.run(cypher, article_id=article_id, limit=limit)

    related_list: List[RelatedArticle] = []
    for rec in records:
        other_node = rec["other"]
        # Il peut ne pas y avoir d'autres articles liés
        if other_node is None:
            continue
        score = rec["score"] if rec["score"] is not None else 0.0
        related_list.append(
            RelatedArticle(
                article=_node_to_article(other_node),
                score=float(score),
            )
        )

    return RelatedArticlesResponse(article_id=article_id, related=related_list)
