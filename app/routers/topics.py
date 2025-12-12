# app/routers/topics.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Topic,
    Article,
    Author,
    TopicGraphResponse,
)

router = APIRouter(prefix="/api", tags=["topics"])


def _node_to_topic(node) -> Topic:
    return Topic(
        name=node.get("name"),
        description=node.get("description"),
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


def _node_to_author(node) -> Author:
    return Author(
        id=node.get("id"),
        name=node.get("name"),
        affiliation=node.get("affiliation"),
    )


@router.get(
    "/topics/{topic_id}/graph",
    response_model=TopicGraphResponse,
)
def get_topic_graph(
    topic_id: str = Path(..., description="Topic identifier (we use the 'name' property)"),
    depth: int = Query(1, ge=1, le=2, description="Currently only 1 hop is used."),
    db: Session = Depends(get_db),
):
    """
    Récupère un sous-graphe autour d'un topic :
    - le topic principal
    - les topics liés
    - les articles associés
    - les auteurs de ces articles
    (Pour simplifier, on ignore 'depth' au-delà de 1 hop.)
    """

    # Vérifier l'existence du topic
    topic_record = db.run(
        "MATCH (t:Topic {name: $name}) RETURN t LIMIT 1", name=topic_id
    ).single()
    if topic_record is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    topic_node = topic_record["t"]
    topic = _node_to_topic(topic_node)

    cypher = """
    MATCH (t:Topic {name: $name})
    OPTIONAL MATCH (t)-[:RELATED_TO_TOPIC]-(rt:Topic)
    OPTIONAL MATCH (t)<-[:HAS_TOPIC]-(a:Article)
    OPTIONAL MATCH (a)-[:WRITTEN_BY]->(au:Author)
    RETURN
        collect(DISTINCT rt)  AS related_topics,
        collect(DISTINCT a)   AS articles,
        collect(DISTINCT au)  AS authors
    """

    record = db.run(cypher, name=topic_id).single()

    related_topics_nodes = record["related_topics"] or []
    article_nodes = record["articles"] or []
    author_nodes = record["authors"] or []

    related_topics: List[Topic] = [
        _node_to_topic(n) for n in related_topics_nodes if n is not None
    ]
    articles: List[Article] = [
        _node_to_article(n) for n in article_nodes if n is not None
    ]
    authors: List[Author] = [
        _node_to_author(n) for n in author_nodes if n is not None
    ]

    return TopicGraphResponse(
        topic=topic,
        related_topics=related_topics,
        articles=articles,
        authors=authors,
    )
