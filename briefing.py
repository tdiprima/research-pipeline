import json
import logging
from datetime import datetime, timezone

from config import BRIEFINGS_DIR
from storage import fetch_recent_articles
from trends import detect_trends, get_category_breakdown

logger = logging.getLogger(__name__)


def generate_briefing(days=7, ollama_available=False):
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    articles = fetch_recent_articles(days=days, min_relevance=0.01)
    trend_report = detect_trends(days=30)
    category_counts = get_category_breakdown(days=days)

    sections = []
    sections.append(f"# AI & DevSecOps Research Briefing — {date_str}\n")
    sections.append(f"*Generated {now.strftime('%Y-%m-%d %H:%M UTC')} "
                    f"| {len(articles)} relevant articles from the last {days} days*\n")

    if not ollama_available:
        sections.append("> **Note:** Ollama was not available. "
                        "Summaries are content snippets, not LLM-generated.\n")

    sections.append(build_highlights_section(articles))
    sections.append(build_by_category_section(articles))
    sections.append(build_trends_section(trend_report))
    sections.append(build_source_breakdown_section(category_counts))

    content = "\n".join(sections)
    output_path = BRIEFINGS_DIR / f"briefing-{date_str}.md"
    output_path.write_text(content, encoding="utf-8")
    logger.info("Briefing written to %s", output_path)
    return output_path


def build_highlights_section(articles, max_highlights=10):
    lines = ["## Top Highlights\n"]
    top_articles = articles[:max_highlights]

    if not top_articles:
        lines.append("*No relevant articles found in this period.*\n")
        return "\n".join(lines)

    for article in top_articles:
        title = article["title"]
        url = article["url"]
        source = article["source_name"]
        score = article["relevance_score"]
        summary = article.get("summary") or ""
        topics_raw = article.get("topics_json")

        lines.append(f"### [{title}]({url})")
        lines.append(f"**Source:** {source} | **Relevance:** {score:.2f}\n")

        if summary:
            lines.append(f"{summary}\n")

        if topics_raw:
            try:
                topic_list = json.loads(topics_raw)
                if topic_list:
                    tags = ", ".join(f"`{t}`" for t in topic_list)
                    lines.append(f"**Topics:** {tags}\n")
            except (json.JSONDecodeError, TypeError):
                pass

        lines.append("---\n")

    return "\n".join(lines)


def build_by_category_section(articles):
    lines = ["## Articles by Category\n"]
    grouped = {}
    for article in articles:
        cat = article.get("source_category", "unknown")
        grouped.setdefault(cat, []).append(article)

    if not grouped:
        lines.append("*No articles to categorize.*\n")
        return "\n".join(lines)

    for category, cat_articles in sorted(grouped.items()):
        display_name = category.replace("_", " ").title()
        lines.append(f"### {display_name} ({len(cat_articles)})\n")
        for article in cat_articles[:10]:
            title = article["title"][:100]
            url = article["url"]
            source = article["source_name"]
            lines.append(f"- [{title}]({url}) — *{source}*")
        if len(cat_articles) > 10:
            lines.append(f"- *...and {len(cat_articles) - 10} more*")
        lines.append("")

    return "\n".join(lines)


def build_trends_section(trend_report):
    lines = ["## Trending Topics (30-day window)\n"]

    has_any = any(trend_report.get(k) for k in ("rising", "sustained", "new"))
    if not has_any:
        lines.append("*Not enough data yet. Run the pipeline a few times to build trend history.*\n")
        return "\n".join(lines)

    if trend_report["sustained"]:
        lines.append("**Sustained topics** (5+ occurrences):")
        for topic in trend_report["sustained"]:
            lines.append(f"- `{topic['name']}` — seen {topic['occurrence_count']} times")
        lines.append("")

    if trend_report["rising"]:
        lines.append("**Rising topics** (2-4 occurrences):")
        for topic in trend_report["rising"]:
            lines.append(f"- `{topic['name']}` — seen {topic['occurrence_count']} times")
        lines.append("")

    if trend_report["new"]:
        lines.append("**Newly appeared:**")
        for topic in trend_report["new"]:
            lines.append(f"- `{topic['name']}`")
        lines.append("")

    return "\n".join(lines)


def build_source_breakdown_section(category_counts):
    lines = ["## Source Breakdown\n"]
    if not category_counts:
        lines.append("*No data.*\n")
        return "\n".join(lines)

    lines.append("| Category | Articles |")
    lines.append("|----------|----------|")
    for category, count in category_counts.items():
        display_name = category.replace("_", " ").title()
        lines.append(f"| {display_name} | {count} |")
    lines.append("")

    return "\n".join(lines)
