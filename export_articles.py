#!/usr/bin/env python3
"""Export articles from research.db for a single day to a Markdown file."""
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "research.db"
EXPORT_DIR = Path(__file__).resolve().parent


def fetch_available_dates(conn):
    """Return distinct dates (YYYY-MM-DD) that have articles, newest first."""
    cursor = conn.execute(
        "SELECT DISTINCT DATE(fetched_at) AS day FROM articles ORDER BY day DESC LIMIT 30"
    )
    return [row[0] for row in cursor.fetchall()]


def fetch_articles_for_date(conn, target_date):
    """Return all articles fetched on target_date (YYYY-MM-DD string)."""
    cursor = conn.execute(
        """SELECT title, url, summary
           FROM articles
           WHERE DATE(fetched_at) = ?
           ORDER BY fetched_at DESC""",
        (target_date,),
    )
    return cursor.fetchall()


def prompt_for_date(available_dates):
    """Interactively ask the user which date to export; return YYYY-MM-DD."""
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if available_dates:
        print("Available dates in database:")
        for day in available_dates[:10]:
            print(f"  {day}")
        if len(available_dates) > 10:
            print(f"  ... and {len(available_dates) - 10} more")

    print(
        f"\nEnter a date to export (YYYY-MM-DD), "
        f"'today' ({today}), or 'yesterday' ({yesterday})."
    )
    raw = input("Date [today]: ").strip()

    if not raw or raw.lower() == "today":
        return today
    if raw.lower() == "yesterday":
        return yesterday

    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        print(f"ERROR: '{raw}' is not a valid date. Use YYYY-MM-DD format.", file=sys.stderr)
        sys.exit(1)


def format_article(title, url, summary):
    """Format one article as a Markdown block."""
    lines = [f"### {title}", f"<{url}>"]
    lines.append(summary if summary else "*No summary available.*")
    return "\n".join(lines)


def main():
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        available_dates = fetch_available_dates(conn)
        target_date = prompt_for_date(available_dates)
        rows = fetch_articles_for_date(conn, target_date)
    finally:
        conn.close()

    if not rows:
        print(f"No articles found for {target_date}.", file=sys.stderr)
        sys.exit(0)

    output_path = EXPORT_DIR / f"articles_export_{target_date}.md"
    blocks = [format_article(title, url, summary) for title, url, summary in rows]
    content = f"# Articles — {target_date}\n\n" + "\n\n\n".join(blocks) + "\n"

    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(rows)} articles to {output_path}")


if __name__ == "__main__":
    main()
