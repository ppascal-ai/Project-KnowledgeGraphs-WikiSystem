# scripts/seed_data.py

import os
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv


def get_driver():
    """
    Crée un driver Neo4j à partir des variables d'environnement.
    Ce script est indépendant de l'app FastAPI pour rester simple.
    """
    load_dotenv()  # charge .env quand on lance le script en local

    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
    return driver


def create_constraints_and_indexes(session):
    """
    Crée les contraintes et index nécessaires pour le modèle Wiki / Knowledge Graph.
    """
    queries = [
        # Unicité
        """
        CREATE CONSTRAINT article_id_unique IF NOT EXISTS
        FOR (a:Article)
        REQUIRE a.id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT topic_name_unique IF NOT EXISTS
        FOR (t:Topic)
        REQUIRE t.name IS UNIQUE
        """,
        """
        CREATE CONSTRAINT author_id_unique IF NOT EXISTS
        FOR (au:Author)
        REQUIRE au.id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT tag_name_unique IF NOT EXISTS
        FOR (tag:Tag)
        REQUIRE tag.name IS UNIQUE
        """,
        """
        CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
        FOR (c:Concept)
        REQUIRE c.id IS UNIQUE
        """,
        # Index simples (facilitent la recherche)
        """
        CREATE INDEX topic_name_index IF NOT EXISTS
        FOR (t:Topic)
        ON (t.name)
        """,
        """
        CREATE INDEX article_title_index IF NOT EXISTS
        FOR (a:Article)
        ON (a.title)
        """,
        """
        CREATE INDEX tag_name_index IF NOT EXISTS
        FOR (tag:Tag)
        ON (tag.name)
        """
    ]

    for q in queries:
        q_clean = q.strip()
        if not q_clean:
            continue
        print(f"[Neo4j] Running constraint/index query:\n{q_clean}\n")
        session.run(q_clean)


def clear_database(session):
    """
    Optionnel : supprime toutes les données existantes.
    À utiliser seulement en dev.
    """
    print("[Neo4j] Clearing existing data (MATCH (n) DETACH DELETE n)")
    session.run("MATCH (n) DETACH DELETE n")


def seed_sample_data(session):
    """
    Insère quelques Topics, Authors, Tags, Articles et relations pour tester l'API.
    """
    print("[Neo4j] Seeding sample data...")

    cypher = """
    // Topics
    MERGE (t_ai:Topic {name: 'Artificial Intelligence'})
      ON CREATE SET t_ai.description = 'Study of intelligent agents and systems.'

    MERGE (t_kg:Topic {name: 'Knowledge Graphs'})
      ON CREATE SET t_kg.description = 'Graphs that store entities and their relationships.'

    MERGE (t_ml:Topic {name: 'Machine Learning'})
      ON CREATE SET t_ml.description = 'Algorithms that learn from data.'

    MERGE (t_nlp:Topic {name: 'Natural Language Processing'})
      ON CREATE SET t_nlp.description = 'Processing and understanding human language.'

    // Topics related
    MERGE (t_ai)-[:RELATED_TO_TOPIC]->(t_ml)
    MERGE (t_ml)-[:RELATED_TO_TOPIC]->(t_ai)
    MERGE (t_ai)-[:RELATED_TO_TOPIC]->(t_kg)
    MERGE (t_kg)-[:RELATED_TO_TOPIC]->(t_ai)
    MERGE (t_ml)-[:RELATED_TO_TOPIC]->(t_nlp)
    MERGE (t_nlp)-[:RELATED_TO_TOPIC]->(t_ml)

    // Authors
    MERGE (a1:Author {id: 'author-1'})
      ON CREATE SET a1.name = 'Alice Smith',
                    a1.affiliation = 'Research Lab X'

    MERGE (a2:Author {id: 'author-2'})
      ON CREATE SET a2.name = 'Bob Johnson',
                    a2.affiliation = 'University Y'

    MERGE (a3:Author {id: 'author-3'})
      ON CREATE SET a3.name = 'Carol Lee',
                    a3.affiliation = 'Data Science Team Z'

    // Author expertise (optionnel mais utile pour les contributions)
    MERGE (a1)-[:EXPERT_IN]->(t_kg)
    MERGE (a1)-[:EXPERT_IN]->(t_ai)
    MERGE (a2)-[:EXPERT_IN]->(t_ml)
    MERGE (a3)-[:EXPERT_IN]->(t_nlp)

    // Tags
    MERGE (tag_graph:Tag {name: 'graph'})
    MERGE (tag_reco:Tag {name: 'recommendation'})
    MERGE (tag_nlp:Tag {name: 'nlp'})
    MERGE (tag_search:Tag {name: 'search'})
    MERGE (tag_kg:Tag {name: 'knowledge-graph'})

    // Articles
    MERGE (art1:Article {id: 'article-1'})
      ON CREATE SET art1.title = 'Building a Company Knowledge Graph',
                    art1.summary = 'How to design and deploy a knowledge graph for internal documentation.',
                    art1.url = 'https://example.com/article-1',
                    art1.source = 'demo',
                    art1.language = 'en'

    MERGE (art2:Article {id: 'article-2'})
      ON CREATE SET art2.title = 'Introduction to Knowledge Graphs',
                    art2.summary = 'Core concepts and use cases for knowledge graphs.',
                    art2.url = 'https://example.com/article-2',
                    art2.source = 'demo',
                    art2.language = 'en'

    MERGE (art3:Article {id: 'article-3'})
      ON CREATE SET art3.title = 'Using Graphs for Semantic Search',
                    art3.summary = 'Leverage graph structures to provide semantic search in an enterprise wiki.',
                    art3.url = 'https://example.com/article-3',
                    art3.source = 'demo',
                    art3.language = 'en'

    // Article ↔️ Topic
    MERGE (art1)-[:HAS_TOPIC]->(t_kg)
    MERGE (art1)-[:HAS_TOPIC]->(t_ai)

    MERGE (art2)-[:HAS_TOPIC]->(t_kg)

    MERGE (art3)-[:HAS_TOPIC]->(t_ai)
    MERGE (art3)-[:HAS_TOPIC]->(t_nlp)

    // Article ↔️ Tags
    MERGE (art1)-[:HAS_TAG]->(tag_kg)
    MERGE (art1)-[:HAS_TAG]->(tag_graph)
    MERGE (art1)-[:HAS_TAG]->(tag_search)

    MERGE (art2)-[:HAS_TAG]->(tag_kg)

    MERGE (art3)-[:HAS_TAG]->(tag_graph)
    MERGE (art3)-[:HAS_TAG]->(tag_reco)
    MERGE (art3)-[:HAS_TAG]->(tag_nlp)

    // Article ↔️ Author
    MERGE (art1)-[:WRITTEN_BY]->(a1)
    MERGE (art2)-[:WRITTEN_BY]->(a1)
    MERGE (art2)-[:WRITTEN_BY]->(a2)
    MERGE (art3)-[:WRITTEN_BY]->(a3)

    // Articles related (suggestions)
    MERGE (art1)-[:RELATED_ARTICLE {score: 0.9}]->(art2)
    MERGE (art2)-[:RELATED_ARTICLE {score: 0.9}]->(art1)
    MERGE (art1)-[:RELATED_ARTICLE {score: 0.7}]->(art3)
    MERGE (art3)-[:RELATED_ARTICLE {score: 0.7}]->(art1)
    """

    session.run(cypher)
    print("[Neo4j] Sample data seeded successfully.")


def main(reset_db: bool = True):
    driver = get_driver()
    with driver.session() as session:
        if reset_db:
            clear_database(session)

        create_constraints_and_indexes(session)
        seed_sample_data(session)

    driver.close()
    print("[Neo4j] Seeding finished.")


if __name__ == "__main__":
    # En dev, on reset tout par défaut ; tu peux passer False si tu ne veux pas tout supprimer
    main(reset_db=True)