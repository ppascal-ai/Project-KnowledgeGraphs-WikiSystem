# app/routers/authors.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Author,
    Article,
    Topic,
    Tag,
    AuthorContributionsResponse,
)

router = APIRouter(prefix="/api", tags=["authors"])


def _node_to_author(node) -> Author:
    return Author(
        id=node.get("id"),
        name=node.get("name"),
        affiliation=node.get("affiliation"),
    )


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
    return Tag(
        name=node.get("name"),
    )


@router.get(
    "/authors/{author_id}/contributions",
    response_model=AuthorContributionsResponse,
)
def get_author_contributions(
    author_id: str = Path(..., description="Author id"),
    db: Session = Depends(get_db),
):
    """
    Renvoie les contributions d'un auteur :
    - Articles écrits
    - Topics associés à ces articles
    - Tags associés
    """

    # Vérifier que l'auteur existe
    author_record = db.run(
        "MATCH (a:Author {id: $id}) RETURN a LIMIT 1", id=author_id
    ).single()
    if author_record is None:
        raise HTTPException(status_code=404, detail="Author not found.")

    author_node = author_record["a"]
    author = _node_to_author(author_node)

    cypher = """
    MATCH (au:Author {id: $id})
    OPTIONAL MATCH (au)<-[:WRITTEN_BY]-(art:Article)
    OPTIONAL MATCH (art)-[:HAS_TOPIC]->(t:Topic)
    OPTIONAL MATCH (art)-[:HAS_TAG]->(tag:Tag)
    RETURN
        collect(DISTINCT art) AS articles,
        collect(DISTINCT t)   AS topics,
        collect(DISTINCT tag) AS tags
    """

    record = db.run(cypher, id=author_id).single()

    article_nodes = record["articles"] or []
    topic_nodes = record["topics"] or []
    tag_nodes = record["tags"] or []

    articles: List[Article] = [
        _node_to_article(a) for a in article_nodes if a is not None
    ]
    topics: List[Topic] = [
        _node_to_topic(t) for t in topic_nodes if t is not None
    ]
    tags: List[Tag] = [
        _node_to_tag(t) for t in tag_nodes if t is not None
    ]

    return AuthorContributionsResponse(
        author=author,
        articles=articles,
        topics=topics,
        tags=tags,
    )
