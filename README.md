# Research Pipeline

Automated research assistant for AI, security, and DevSecOps intelligence gathering.

Instead of doomscrolling through fragmented feeds, this pipeline collects curated sources, filters for relevance, summarizes important content, tracks trends over time, and generates a daily Markdown briefing.

---

## Features

- Curated RSS feeds (Reddit, ArXiv, CISA, Hacker News, Snyk, Trail of Bits, Hugging Face, etc.)
- Keyword-based relevance scoring for AI + DevSecOps topics
- Local LLM summarization using Ollama + Gemma
- SQLite persistence for historical topic tracking
- Trend detection across multiple runs
- Daily Markdown briefing generation

---

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | Orchestrates the full pipeline |
| `sources.py` | Curated RSS feed definitions |
| `collector.py` | RSS fetching + parsing |
| `relevance.py` | Relevance scoring |
| `storage.py` | SQLite persistence |
| `summarizer.py` | Ollama summarization |
| `trends.py` | Topic trend detection |
| `briefing.py` | Markdown briefing generation |
| `config.py` | Environment-based configuration |

---

## Usage

```bash
cd research-pipeline

# Full pipeline
python main.py

# Skip LLM summarization
python main.py --no-llm

# Regenerate briefing from existing DB
python main.py --briefing

# Limit processing window
python main.py --days 3
```

---

## Notes

- ArXiv feeds are typically empty on Sundays.
- Trend tracking improves as the database accumulates historical runs.
- Ollama is optional but recommended.

---

## Stack

- Python
- SQLite
- Ollama
- RSS feeds
- Markdown reporting
