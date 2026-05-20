import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from html import unescape

import feedparser
import requests

from config import FETCH_TIMEOUT_SECONDS, MAX_ARTICLE_AGE_DAYS, MAX_ARTICLES_PER_FEED, MAX_RESPONSE_BYTES

logger = logging.getLogger(__name__)

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def strip_html(text):
    if not text:
        return ""
    cleaned = HTML_TAG_PATTERN.sub(" ", text)
    cleaned = unescape(cleaned)
    return " ".join(cleaned.split())


def generate_article_id(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def parse_published_date(entry):
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        except (ValueError, TypeError):
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()
        except (ValueError, TypeError):
            pass
    return None


def is_recent_enough(published_at, max_age_days):
    if not published_at:
        # return False
        return True  # Articles with no published_at now pass through
    try:
        published_dt = datetime.fromisoformat(published_at)
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        return published_dt >= cutoff
    except (ValueError, TypeError):
        return False


def extract_content_snippet(entry, max_length=2000):
    content = ""
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].get("value", "")
    elif hasattr(entry, "summary"):
        content = entry.summary or ""
    elif hasattr(entry, "description"):
        content = entry.description or ""
    return strip_html(content)[:max_length]


def fetch_single_feed(feed_config):
    feed_name = feed_config["name"]
    feed_url = feed_config["url"]
    category = feed_config["category"]
    articles = []

    try:
        response = requests.get(
            feed_url,
            timeout=FETCH_TIMEOUT_SECONDS,
            headers={"User-Agent": "ResearchPipeline/1.0"},
            stream=True,
        )
        response.raise_for_status()

        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_RESPONSE_BYTES:
            logger.warning(
                "Feed %s too large (%s bytes), skipping", feed_name, content_length
            )
            response.close()
            return articles

        chunks = []
        bytes_read = 0
        for chunk in response.iter_content(chunk_size=65536):
            bytes_read += len(chunk)
            if bytes_read > MAX_RESPONSE_BYTES:
                logger.warning("Feed %s exceeded %d bytes during read, truncating", feed_name, MAX_RESPONSE_BYTES)
                break
            chunks.append(chunk)
        response.close()
        content = b"".join(chunks)
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", feed_name, exc)
        return articles

    parsed = feedparser.parse(content)

    if parsed.bozo and not parsed.entries:
        logger.warning("Malformed feed from %s: %s", feed_name, parsed.bozo_exception)
        return articles

    now = datetime.now(timezone.utc).isoformat()

    for entry in parsed.entries[:MAX_ARTICLES_PER_FEED]:
        url = getattr(entry, "link", None)
        title = getattr(entry, "title", None)
        if not url or not title:
            continue

        published_at = parse_published_date(entry)
        if not is_recent_enough(published_at, MAX_ARTICLE_AGE_DAYS):
            continue

        articles.append({
            "id": generate_article_id(url),
            "url": url,
            "title": strip_html(title),
            "source_name": feed_name,
            "source_category": category,
            "published_at": published_at,
            "fetched_at": now,
            "content_snippet": extract_content_snippet(entry),
        })

    logger.info("Fetched %d articles from %s", len(articles), feed_name)
    return articles


def fetch_all_feeds(feeds):
    all_articles = []
    for feed_config in feeds:
        articles = fetch_single_feed(feed_config)
        all_articles.extend(articles)
    logger.info("Total articles fetched: %d", len(all_articles))
    return all_articles
