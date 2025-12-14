# app/routers/search.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Topic,
    Tag,
    Article,
    ArticleWithContext,
    SearchResponse,
)

router = APIRouter(prefix="/api", tags=["search"])


def _node_to_article(node) -> Article:
    return Article(
        id=node.get("id"),
        title=node.get("title"),
        summary=node.get("summary"),
        url=node.get("url"),
        source=node.get("source"),
        language=node.get("language"),
    )


def _node_to_topic(node) -> Topic:
    return Topic(
        name=node.get("name"),
        description=node.get("description"),
    )


def _node_to_tag(node) -> Tag:
    return Tag(name=node.get("name"))


@router.get("/search", response_model=SearchResponse)
def search_articles(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Recherche simple dans les titres / résumés / topics / tags.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' must not be empty.")

    cypher = """
    MATCH (a:Article)
    OPTIONAL MATCH (a)-[:HAS_TOPIC]->(t:Topic)
    OPTIONAL MATCH (a)-[:HAS_TAG]->(tag:Tag)
    WHERE toLower(a.title) CONTAINS toLower($q)
       OR toLower(coalesce(a.summary, '')) CONTAINS toLower($q)
       OR toLower(coalesce(t.name, '')) CONTAINS toLower($q)
       OR toLower(coalesce(tag.name, '')) CONTAINS toLower($q)
    RETURN a,
           collect(DISTINCT t)   AS topics,
           collect(DISTINCT tag) AS tags
    LIMIT $limit
    """

    records = db.run(cypher, q=q, limit=limit)

    results: List[ArticleWithContext] = []
    for record in records:
        article_node = record["a"]
        topic_nodes = record["topics"] or []
        tag_nodes = record["tags"] or []

        article = _node_to_article(article_node)
        topics = [_node_to_topic(t) for t in topic_nodes if t is not None]
        tags = [_node_to_tag(t) for t in tag_nodes if t is not None]

        results.append(
            ArticleWithContext(
                **article.model_dump(),
                topics=topics,
                tags=tags,
            )
        )

    return SearchResponse(query=q, results=results)
