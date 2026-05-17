import logging
import re

from config import RELEVANCE_KEYWORDS

logger = logging.getLogger(__name__)

KEYWORD_PATTERNS = [
    re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
    for kw in RELEVANCE_KEYWORDS
]


def score_article(article):
    searchable_text = " ".join([
        article.get("title", ""),
        article.get("content_snippet", ""),
        article.get("source_category", ""),
    ]).lower()

    matched_keywords = []
    for pattern, keyword in zip(KEYWORD_PATTERNS, RELEVANCE_KEYWORDS):
        if pattern.search(searchable_text):
            matched_keywords.append(keyword)

    if not matched_keywords:
        return 0.0, matched_keywords

    base_score = len(matched_keywords) / len(RELEVANCE_KEYWORDS)

    title_lower = article.get("title", "").lower()
    title_matches = sum(
        1 for p in KEYWORD_PATTERNS if p.search(title_lower)
    )
    title_bonus = min(title_matches * 0.1, 0.3)

    category = article.get("source_category", "")
    category_bonus = 0.15 if category in ("devsecops", "appsec_tools") else 0.0

    score = min(base_score + title_bonus + category_bonus, 1.0)
    return round(score, 3), matched_keywords


def filter_articles(articles, min_score=0.01):
    scored_articles = []
    for article in articles:
        score, matched_keywords = score_article(article)
        article["relevance_score"] = score
        article["matched_keywords"] = matched_keywords
        if score >= min_score:
            scored_articles.append(article)

    scored_articles.sort(key=lambda a: a["relevance_score"], reverse=True)
    logger.info(
        "Filtered %d relevant articles from %d total",
        len(scored_articles),
        len(articles),
    )
    return scored_articles
