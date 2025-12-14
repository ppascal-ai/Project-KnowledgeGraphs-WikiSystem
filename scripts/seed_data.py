# scripts/seed_data.py
import os
import json
import math
import argparse
from typing import Dict, List, Iterable, Tuple

import pandas as pd
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv



# Connection

def get_driver():
    """
    Create a Neo4j driver from environment variables.
    This seeding script is independent from the FastAPI app.
    """
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    return GraphDatabase.driver(uri, auth=basic_auth(user, password))



# Schema (constraints/indexes)

def create_constraints_and_indexes(session):
    """
    Create constraints and indexes for the Wiki / Knowledge Graph model.
    """
    queries = [
        # Uniqueness constraints
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
        # Indexes
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
        """,
        # Optional but useful for analytics/search on traffic
        """
        CREATE INDEX article_traffic_index IF NOT EXISTS
        FOR (a:Article)
        ON (a.traffic)
        """,
    ]

    for q in queries:
        q_clean = q.strip()
        if q_clean:
            print(f"[Neo4j] Running constraint/index query:\n{q_clean}\n")
            session.run(q_clean)


def clear_database(session):
    """
    DEV ONLY: delete everything.
    """
    print("[Neo4j] Clearing existing data (MATCH (n) DETACH DELETE n)")
    session.run("MATCH (n) DETACH DELETE n")



# Helpers (batching)

def chunked(items: List, size: int) -> Iterable[List]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def ensure_topic_and_authors(session):
    """
    Create the single Topic + a few Authors (synthetic) to keep the existing API model consistent.
    """
    cypher = """
    MERGE (t:Topic {name: $topic_name})
      ON CREATE SET t.description = $topic_desc

    // 3 authors to distribute WRITTEN_BY deterministically
    MERGE (a1:Author {id: "author-1"})
      ON CREATE SET a1.name = "Wikipedia Bot A", a1.affiliation = "Wikipedia (dataset)"
    MERGE (a2:Author {id: "author-2"})
      ON CREATE SET a2.name = "Wikipedia Bot B", a2.affiliation = "Wikipedia (dataset)"
    MERGE (a3:Author {id: "author-3"})
      ON CREATE SET a3.name = "Wikipedia Bot C", a3.affiliation = "Wikipedia (dataset)"

    // Optional expertise links (your endpoints can use it)
    MERGE (a1)-[:EXPERT_IN]->(t)
    MERGE (a2)-[:EXPERT_IN]->(t)
    MERGE (a3)-[:EXPERT_IN]->(t)
    """
    session.run(
        cypher,
        topic_name="Squirrel",
        topic_desc="Wikipedia page-page network about squirrels (MUSAE dataset).",
    )


# -------------------------
# Dataset loading
# -------------------------
def load_squirrel_dataset(dataset_dir: str) -> Tuple[pd.DataFrame, Dict[str, List[int]], pd.DataFrame]:
    """
    Expects:
      - musae_squirrel_edges.csv (id1,id2)
      - musae_squirrel_features.json (node_id -> [feature_id,...])
      - musae_squirrel_target.csv (id,target)
    """
    edges_path = os.path.join(dataset_dir, "musae_squirrel_edges.csv")
    features_path = os.path.join(dataset_dir, "musae_squirrel_features.json")
    target_path = os.path.join(dataset_dir, "musae_squirrel_target.csv")

    if not os.path.exists(edges_path):
        raise FileNotFoundError(f"Missing {edges_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Missing {features_path}")
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Missing {target_path}")

    edges_df = pd.read_csv(edges_path)
    targets_df = pd.read_csv(target_path)

    with open(features_path, "r", encoding="utf-8") as f:
        features_map: Dict[str, List[int]] = json.load(f)

    # Basic validation
    if not {"id1", "id2"}.issubset(edges_df.columns):
        raise ValueError("edges.csv must contain columns: id1,id2")
    if not {"id", "target"}.issubset(targets_df.columns):
        raise ValueError("target.csv must contain columns: id,target")

    return edges_df, features_map, targets_df



# Seeding (Neo4j)

def seed_articles(session, targets_df: pd.DataFrame, batch_size: int = 2000):
    """
    Create Article nodes with traffic (target) and link each to Topic(Squirrel) + one Author.
    """
    print(f"[Neo4j] Creating Article nodes from target.csv (rows={len(targets_df)})...")

    # Build rows for UNWIND
    rows: List[Dict] = []
    for _, r in targets_df.iterrows():
        node_id = str(int(r["id"]))
        traffic = float(r["target"])
        author_pick = (int(node_id) % 3) + 1  # 1..3
        rows.append(
            {
                "id": node_id,
                "title": f"Wikipedia Page {node_id}",
                "summary": None,
                "url": None,
                "source": "musae_squirrel",
                "language": "en",
                "traffic": traffic,
                "author_id": f"author-{author_pick}",
            }
        )

    cypher = """
    UNWIND $rows AS row
    MERGE (a:Article {id: row.id})
      ON CREATE SET
        a.title = row.title,
        a.summary = row.summary,
        a.url = row.url,
        a.source = row.source,
        a.language = row.language,
        a.traffic = row.traffic
      ON MATCH SET
        a.traffic = row.traffic

    WITH a, row
    MATCH (t:Topic {name: "Squirrel"})
    MERGE (a)-[:HAS_TOPIC]->(t)

    WITH a, row
    MATCH (au:Author {id: row.author_id})
    MERGE (a)-[:WRITTEN_BY]->(au)
    """

    for batch in chunked(rows, batch_size):
        session.run(cypher, rows=batch)

    print("[Neo4j] Articles seeded.")


def seed_tags_and_article_tags(
    session,
    features_map: Dict[str, List[int]],
    batch_size: int = 1000,
    max_tags_per_article: int = 40,
):
    """
    Create Tag nodes and HAS_TAG relationships from features.json.
    To keep it manageable, we cap tags per article (default 40).
    """
    print(f"[Neo4j] Creating Tags + HAS_TAG relationships from features.json (articles={len(features_map)})...")

    rows: List[Dict] = []
    for node_id_str, feats in features_map.items():
        # some files can contain strings already, keep consistent with Article.id
        article_id = str(int(node_id_str))
        feats_limited = feats[:max_tags_per_article] if feats else []
        for feat_id in feats_limited:
            rows.append(
                {
                    "article_id": article_id,
                    "tag_name": f"feat_{int(feat_id)}",
                }
            )

    cypher = """
    UNWIND $rows AS row
    MATCH (a:Article {id: row.article_id})
    MERGE (t:Tag {name: row.tag_name})
    MERGE (a)-[:HAS_TAG]->(t)
    """

    for batch in chunked(rows, batch_size):
        session.run(cypher, rows=batch)

    print("[Neo4j] Tags seeded.")


def seed_related_articles(
    session,
    edges_df: pd.DataFrame,
    batch_size: int = 5000,
    max_edges: int | None = None,
):
    """
    Create RELATED_ARTICLE relationships from edges.csv.
    We write both directions so your endpoint can find outbound links.
    """
    total_edges = len(edges_df)
    if max_edges is not None:
        total_edges = min(total_edges, max_edges)
        edges_df = edges_df.head(max_edges)

    print(f"[Neo4j] Creating RELATED_ARTICLE relationships from edges.csv (edges={total_edges})...")

    rows: List[Dict] = []
    for _, r in edges_df.iterrows():
        a = str(int(r["id1"]))
        b = str(int(r["id2"]))
        if a == b:
            continue
        rows.append({"a": a, "b": b, "score": 1.0})

    cypher = """
    UNWIND $rows AS row
    MATCH (a:Article {id: row.a})
    MATCH (b:Article {id: row.b})
    MERGE (a)-[r:RELATED_ARTICLE]->(b)
      ON CREATE SET r.score = row.score
      ON MATCH SET r.score = row.score
    """

    for batch in chunked(rows, batch_size):
        session.run(cypher, rows=batch)

    # Add reverse direction too (important if edges are undirected)
    cypher_rev = """
    UNWIND $rows AS row
    MATCH (a:Article {id: row.a})
    MATCH (b:Article {id: row.b})
    MERGE (b)-[r:RELATED_ARTICLE]->(a)
      ON CREATE SET r.score = row.score
      ON MATCH SET r.score = row.score
    """
    for batch in chunked(rows, batch_size):
        session.run(cypher_rev, rows=batch)

    print("[Neo4j] RELATED_ARTICLE relationships seeded.")


# Main

def main():
    parser = argparse.ArgumentParser(description="Seed Neo4j with the MUSAE Squirrel dataset.")
    parser.add_argument(
        "--dataset-dir",
        default=os.getenv("DATASET_DIR", "data/squirrel"),
        help="Folder containing musae_squirrel_edges.csv, musae_squirrel_features.json, musae_squirrel_target.csv",
    )
    parser.add_argument("--no-reset", action="store_true", help="Do not clear the database before seeding")
    parser.add_argument("--max-edges", type=int, default=int(os.getenv("MAX_EDGES", "0")), help="Limit number of edges (0 = no limit)")
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("BATCH_SIZE", "2000")), help="Batch size for UNWIND writes")
    parser.add_argument(
        "--max-tags-per-article",
        type=int,
        default=int(os.getenv("MAX_TAGS_PER_ARTICLE", "40")),
        help="Cap number of tags per article (keeps DB smaller & faster)",
    )
    args = parser.parse_args()

    max_edges = None if args.max_edges == 0 else args.max_edges

    driver = get_driver()
    with driver.session() as session:
        if not args.no_reset:
            clear_database(session)

        create_constraints_and_indexes(session)
        ensure_topic_and_authors(session)

        edges_df, features_map, targets_df = load_squirrel_dataset(args.dataset_dir)

        seed_articles(session, targets_df, batch_size=args.batch_size)
        seed_tags_and_article_tags(
            session,
            features_map,
            batch_size=max(5000, args.batch_size),
            max_tags_per_article=args.max_tags_per_article,
        )
        seed_related_articles(
            session,
            edges_df,
            batch_size=max(5000, args.batch_size),
            max_edges=max_edges,
        )

    driver.close()
    print("[Neo4j] Seeding finished.")


if __name__ == "__main__":
    main()
