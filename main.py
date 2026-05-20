#!/usr/bin/env python3
"""
AI & DevSecOps Research Pipeline

Fetches articles from curated RSS feeds, filters by relevance,
optionally summarizes via Ollama (gemma4), stores in SQLite,
and generates a Markdown briefing with trend tracking.

Usage:
    python main.py              # Full pipeline
    python main.py --no-llm     # Skip LLM summarization
    python main.py --briefing   # Generate briefing from existing data only
    python main.py --days 3     # Articles from last 3 days (default: 7)
"""
import argparse
import logging
import sys

from collector import fetch_all_feeds
from relevance import filter_articles
from storage import initialize_database, insert_articles, fetch_unsummarized_articles, get_existing_article_ids, update_article_summary
from summarizer import check_ollama_available, summarize_batch
from briefing import generate_briefing
from sources import FEEDS


def configure_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="AI & DevSecOps Research Pipeline",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM summarization even if Ollama is available",
    )
    parser.add_argument(
        "--briefing",
        action="store_true",
        help="Only generate briefing from existing data (skip fetch/summarize)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to include in the briefing (default: 7)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def run_collection_phase():
    logger = logging.getLogger("pipeline")
    logger.info("Fetching articles from %d feeds...", len(FEEDS))
    raw_articles = fetch_all_feeds(FEEDS)

    candidate_ids = [a["id"] for a in raw_articles]
    existing_ids = get_existing_article_ids(candidate_ids) if candidate_ids else set()
    new_articles = [a for a in raw_articles if a["id"] not in existing_ids]
    logger.info("Skipped %d already-stored articles", len(raw_articles) - len(new_articles))

    logger.info("Scoring relevance on %d new articles...", len(new_articles))
    relevant_articles = filter_articles(new_articles)

    logger.info("Storing %d relevant articles...", len(relevant_articles))
    new_count = insert_articles(relevant_articles)
    logger.info("New articles stored: %d", new_count)
    return new_count


def run_summarization_phase(use_llm):
    logger = logging.getLogger("pipeline")

    if not use_llm:
        logger.info("LLM summarization disabled (--no-llm)")
        return False

    if not check_ollama_available():
        logger.info("Ollama not available — skipping summarization")
        return False

    unsummarized = fetch_unsummarized_articles(limit=50)
    if not unsummarized:
        logger.info("No articles pending summarization")
        return True

    logger.info("Summarizing %d articles with Ollama...", len(unsummarized))
    results = summarize_batch(unsummarized)

    for result in results:
        if result["summary"]:
            update_article_summary(result["id"], result["summary"], result["topics"])

    summarized_count = sum(1 for r in results if r["summary"])
    logger.info("Summarized %d/%d articles", summarized_count, len(results))
    return True


def run_briefing_phase(days, ollama_was_available):
    logger = logging.getLogger("pipeline")
    logger.info("Generating briefing...")
    output_path = generate_briefing(days=days, ollama_available=ollama_was_available)
    logger.info("Briefing ready: %s", output_path)
    return output_path


def main():
    args = parse_arguments()
    configure_logging(args.verbose)
    logger = logging.getLogger("pipeline")

    initialize_database()

    if args.briefing:
        output_path = run_briefing_phase(args.days, ollama_was_available=False)
        print(f"\nBriefing generated: {output_path}")
        return

    run_collection_phase()
    ollama_available = run_summarization_phase(use_llm=not args.no_llm)
    output_path = run_briefing_phase(args.days, ollama_available)

    print(f"\nBriefing generated: {output_path}")


if __name__ == "__main__":
    main()
