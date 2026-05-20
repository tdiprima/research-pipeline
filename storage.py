import json
import logging
import sqlite3
from datetime import datetime, timezone

from config import DB_PATH

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_category TEXT NOT NULL,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    content_snippet TEXT,
    summary TEXT,
    topics_json TEXT,
    relevance_score REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    occurrence_count INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS article_topics (
    article_id TEXT REFERENCES articles(id),
    topic_id INTEGER REFERENCES topics(id),
    PRIMARY KEY (article_id, topic_id)
);

CREATE INDEX IF NOT EXISTS idx_articles_fetched ON articles(fetched_at);
CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score);
CREATE INDEX IF NOT EXISTS idx_topics_count ON topics(occurrence_count DESC);
"""


def get_connection():
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize_database():
    connection = get_connection()
    try:
        connection.executescript(SCHEMA)
        connection.commit()
        logger.info("Database initialized at %s", DB_PATH)
    finally:
        connection.close()


def article_exists(connection, article_id):
    cursor = connection.execute(
        "SELECT 1 FROM articles WHERE id = ?", (article_id,)
    )
    return cursor.fetchone() is not None


def get_existing_article_ids(article_ids):
    connection = get_connection()
    try:
        placeholders = ",".join("?" for _ in article_ids)
        rows = connection.execute(
            f"SELECT id FROM articles WHERE id IN ({placeholders})",
            tuple(article_ids),
        ).fetchall()
        return {row["id"] for row in rows}
    finally:
        connection.close()


def insert_articles(articles):
    connection = get_connection()
    inserted_count = 0
    try:
        for article in articles:
            if article_exists(connection, article["id"]):
                continue
            connection.execute(
                """INSERT INTO articles
                   (id, url, title, source_name, source_category,
                    published_at, fetched_at, content_snippet, relevance_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    article["id"],
                    article["url"],
                    article["title"],
                    article["source_name"],
                    article["source_category"],
                    article.get("published_at"),
                    article["fetched_at"],
                    article.get("content_snippet", ""),
                    article.get("relevance_score", 0.0),
                ),
            )
            inserted_count += 1
        connection.commit()
        logger.info("Inserted %d new articles", inserted_count)
    finally:
        connection.close()
    return inserted_count


def update_article_summary(article_id, summary, topics):
    connection = get_connection()
    try:
        connection.execute(
            "UPDATE articles SET summary = ?, topics_json = ? WHERE id = ?",
            (summary, json.dumps(topics), article_id),
        )
        now = datetime.now(timezone.utc).isoformat()
        for topic_name in topics:
            normalized = topic_name.strip().lower()
            existing = connection.execute(
                "SELECT id FROM topics WHERE name = ?", (normalized,)
            ).fetchone()
            if existing:
                topic_id = existing["id"]
                connection.execute(
                    """UPDATE topics
                       SET last_seen = ?, occurrence_count = occurrence_count + 1
                       WHERE id = ?""",
                    (now, topic_id),
                )
            else:
                cursor = connection.execute(
                    """INSERT INTO topics (name, first_seen, last_seen, occurrence_count)
                       VALUES (?, ?, ?, 1)""",
                    (normalized, now, now),
                )
                topic_id = cursor.lastrowid

            connection.execute(
                """INSERT OR IGNORE INTO article_topics (article_id, topic_id)
                   VALUES (?, ?)""",
                (article_id, topic_id),
            )
        connection.commit()
    finally:
        connection.close()


def fetch_unsummarized_articles(limit=50):
    connection = get_connection()
    try:
        rows = connection.execute(
            """SELECT id, url, title, source_name, source_category,
                      content_snippet, relevance_score
               FROM articles
               WHERE summary IS NULL AND relevance_score > 0
               ORDER BY relevance_score DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def fetch_recent_articles(days=7, min_relevance=0.0):
    connection = get_connection()
    try:
        rows = connection.execute(
            """SELECT id, url, title, source_name, source_category,
                      published_at, summary, topics_json, relevance_score
               FROM articles
               WHERE fetched_at >= datetime('now', ? || ' days')
                 AND relevance_score > ?
               ORDER BY relevance_score DESC, fetched_at DESC""",
            (f"-{days}", min_relevance),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def fetch_trending_topics(days=30, min_occurrences=2):
    connection = get_connection()
    try:
        rows = connection.execute(
            """SELECT name, occurrence_count, first_seen, last_seen
               FROM topics
               WHERE last_seen >= datetime('now', ? || ' days')
                 AND occurrence_count >= ?
               ORDER BY occurrence_count DESC
               LIMIT 20""",
            (f"-{days}", min_occurrences),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
