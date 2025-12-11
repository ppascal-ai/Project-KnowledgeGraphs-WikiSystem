# app/main.py

from fastapi import FastAPI, Depends
from neo4j import Session

from app.database.neo4j import get_db, close_driver


app = FastAPI(
    title="Knowledge Graph / Wiki API",
    description="API pour le projet de Knowledge Graph (Articles, Topics, Authors, Tags, ...)",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check(db: Session = Depends(get_db)):
    """
    Vérifie que l'API tourne et que Neo4j répond.
    """
    result = db.run("RETURN 1 AS ok").single()
    db_ok = bool(result and result.get("ok") == 1)
    return {
        "status": "ok",
        "neo4j": "up" if db_ok else "down",
    }


@app.on_event("shutdown")
def on_shutdown():
    """
    Hook appelé quand l'application s'arrête.
    On ferme le driver Neo4j proprement.
    """
    close_driver()
