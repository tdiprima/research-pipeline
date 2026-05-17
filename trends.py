import logging

from storage import fetch_trending_topics, fetch_recent_articles

logger = logging.getLogger(__name__)


def detect_trends(days=30, min_occurrences=2):
    topics = fetch_trending_topics(days=days, min_occurrences=min_occurrences)
    if not topics:
        logger.info("No trending topics found in the last %d days", days)
        return {"rising": [], "sustained": [], "new": []}

    rising = []
    sustained = []
    new_topics = []

    for topic in topics:
        count = topic["occurrence_count"]
        first_seen = topic["first_seen"]
        last_seen = topic["last_seen"]

        if first_seen == last_seen and count >= min_occurrences:
            new_topics.append(topic)
        elif count >= 5:
            sustained.append(topic)
        elif count >= min_occurrences:
            rising.append(topic)

    trend_report = {
        "rising": rising,
        "sustained": sustained,
        "new": new_topics,
    }

    logger.info(
        "Trends: %d rising, %d sustained, %d new",
        len(rising), len(sustained), len(new_topics),
    )
    return trend_report


def get_category_breakdown(days=7):
    articles = fetch_recent_articles(days=days, min_relevance=0.01)
    categories = {}
    for article in articles:
        cat = article.get("source_category", "unknown")
        categories.setdefault(cat, 0)
        categories[cat] += 1
    return dict(sorted(categories.items(), key=lambda item: item[1], reverse=True))
