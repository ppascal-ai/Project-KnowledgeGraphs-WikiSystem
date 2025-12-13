# Knowledge Graph / Wiki System – Projet AIDAMS 3A

Projet réalisé dans le cadre du cours **“Graph Databases & Knowledge Graphs”**.
L’objectif : construire une **API de Knowledge Graph** basée sur **Neo4j** et **FastAPI**, permettant la recherche, l’exploration de sous-graphes, les recommandations d’articles et l’analyse des contributions d’auteurs.

---

## 👥 **Équipe**

* Paul Pascal (team lead)
* Andrea Surace Gomez
* Toscane Cesbron Darnaud

---

# **1. Objectif du projet**

Développer un système de **wiki / knowledge graph** inspiré d’un environnement de documentation interne en entreprise.

Le système doit permettre :

* La **modélisation** d’articles, auteurs, topics, tags et concepts.
* La **navigation** dans un graphe de connaissances.
* La **recherche sémantique** d’articles.
* La **découverte de contenu lié**.
* La **visualisation des contributions** des auteurs.
* L’exposition d’une API REST propre via **FastAPI**.

Ce projet utilise :

* **Neo4j 5.x** (base de graph orientée relations)
* **Python 3.11**
* **FastAPI** (endpoints REST)
* **Docker / docker-compose**
* **Neo4j Python Driver**
* **pytest** pour les tests unitaires et d’intégration

---

# **2. Architecture du projet**

```
.
├── app
│   ├── main.py
│   ├── database
│   │   └── neo4j.py
│   ├── models
│   │   └── schemas.py
│   └── routers
│       ├── search.py
│       ├── articles.py
│       ├── topics.py
│       └── authors.py
├── scripts
│   └── seed_data.py
├── tests
│   ├── test_health.py
│   ├── test_search.py
│   ├── test_articles.py
│   └── test_authors.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── Makefile
└── .env.example
```

---

# **3. Modèle de graphe Neo4j**

Nous modélisons un écosystème documentaire via les labels :

### **Nœuds (Labels)**

| Label       | Description                                             |
| ----------- | ------------------------------------------------------- |
| **Article** | Contenu principal : titre, résumé, url, langue, source… |
| **Topic**   | Sujet / concept principal rattaché à un article         |
| **Author**  | Auteur(e) ayant écrit des articles                      |
| **Tag**     | Mots-clés associés aux articles                         |
| **Concept** | Entités externes (optionnelles)                         |

### **Relations**

| Relation                                            | Description               |
| --------------------------------------------------- | ------------------------- |
| `(:Article)-[:HAS_TOPIC]->(:Topic)`                 | L’article traite ce sujet |
| `(:Article)-[:HAS_TAG]->(:Tag)`                     | Mots-clés                 |
| `(:Article)-[:WRITTEN_BY]->(:Author)`               | Auteur de l’article       |
| `(:Topic)-[:RELATED_TO_TOPIC]->(:Topic)`            | Topics connexes           |
| `(:Article)-[:RELATED_ARTICLE {score}]->(:Article)` | Articles similaires       |
| `(:Author)-[:EXPERT_IN]->(:Topic)`                  | Domaine d’expertise       |

### **Contraintes & Index**

Créés automatiquement dans `scripts/seed_data.py`.

---

# **4. Population de la base (seed)**

Le script `scripts/seed_data.py` :

* Efface la base (optionnel)
* Crée toutes les contraintes & index
* Insère un dataset simple contenant :

  * Articles et leurs propriétés
  * Topics et leurs relations
  * Tags
  * Auteurs
  * Recommandations d’articles

Exécution :

```bash
make seed
```

---

# **5. Lancement du projet**

## ** After cloning the repository, environment variables must be initialized using the provided .env.example file.**

### **1. Démarrer les services**

```bash
make up
```

Equivalent :

```bash
docker-compose up --build -d
```

---

### **2. Accéder aux services**

| Service               | URL                                                      |
| --------------------- | -------------------------------------------------------- |
| API FastAPI           | [http://localhost:8000](http://localhost:8000)           |
| Documentation Swagger | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Neo4j Browser         | [http://localhost:7474](http://localhost:7474)           |

---

### **3. Peupler Neo4j**

```bash
make seed
```

---

### **4. Exécuter les tests**

```
make test
```

Résultat attendu :

```
4 passed in X.XXs
```

---

# **6. API – Endpoints principaux**

La documentation complète est disponible sur Swagger :
 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## **GET /api/search?q=...**

Recherche d’articles selon :

* titre
* résumé
* topics
* tags

**Exemple :**

```
/api/search?q=graph
```

Renvoie une liste d’articles + leurs topics et tags.

---

## **GET /api/articles/{article_id}/related**

Renvoie les articles liés via `RELATED_ARTICLE` triés par score.

**Exemple :**

```
/api/articles/article-1/related
```

---

## **GET /api/topics/{topic_id}/graph**

Renvoie un sous-graphe composé de :

* le topic principal
* les topics liés
* les articles associés
* les auteurs liés

**Exemple :**

```
/api/topics/Knowledge%20Graphs/graph
```

---

## **GET /api/authors/{author_id}/contributions**

Renvoie :

* articles écrits
* topics associés
* tags associés

**Exemple :**

```
/api/authors/author-1/contributions
```

---

# **7. Tests**

Les tests automatisés couvrent :

* Healthcheck
* Search
* Articles liés
* Contributions auteur

Exécution :

```
make test
```

---

# **8. Choix de design**

* FastAPI pour une API simple, rapide, bien documentée.
* Neo4j pour la modélisation flexible de relations entre entités.
* Docker pour l’isolation et la reproductibilité.
* Makefile pour un workflow clean.
* Tests unitaires et d’intégration via pytest pour valider les endpoints.

---

# **9. Améliorations possibles**

* Ajout d’un **Full-Text Search Index** Neo4j pour meilleure recherche.
* Intégration d’un système d’embeddings (LLM) pour suggestions complexes.
* Interface web de visualisation graphique.
* Ajout d’un pipeline d’ingestion de données réelles Wikidata.

---

# **10. Conclusion**

Ce projet démontre :

* une modélisation fidèle d’un wiki sous forme de graphe,
* une API cohérente et fonctionnelle,
* un environnement reproductible via Docker,
* un code testé et maintenable.
