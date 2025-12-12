# app/models/schemas.py

from typing import List, Optional
from pydantic import BaseModel


# Basic entities

class Topic(BaseModel):
    name: str
    description: Optional[str] = None


class Tag(BaseModel):
    name: str


class Author(BaseModel):
    id: str
    name: str
    affiliation: Optional[str] = None


class Article(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None


# Composite models for API responses

class ArticleWithContext(Article):
    topics: List[Topic] = []
    tags: List[Tag] = []


class SearchResponse(BaseModel):
    query: str
    results: List[ArticleWithContext]


class RelatedArticle(BaseModel):
    article: Article
    score: float


class RelatedArticlesResponse(BaseModel):
    article_id: str
    related: List[RelatedArticle]


class TopicGraphResponse(BaseModel):
    topic: Topic
    related_topics: List[Topic] = []
    articles: List[Article] = []
    authors: List[Author] = []


class AuthorContributionsResponse(BaseModel):
    author: Author
    articles: List[Article] = []
    topics: List[Topic] = []
    tags: List[Tag] = []
