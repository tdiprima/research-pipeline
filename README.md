# KoolAdeOps

Automated research pipeline that pulls AI and DevSecOps articles from 19 curated sources, scores them for relevance, summarizes them with a local LLM, and delivers a daily Markdown briefing — no subscriptions, no cloud API keys required.

## Keeping Up Is a Full-Time Job

The AI security and DevSecOps landscape moves fast. ArXiv drops new papers daily. CISA publishes advisories. Schneier, Krebs, The Hacker News, Reddit communities, and vendor blogs all publish independently. Manually checking each source, filtering signal from noise, and distilling what actually matters takes hours — time most engineers don't have.

## What KoolAdeOps Does

KoolAdeOps runs as a single command. It fetches RSS feeds from 19 sources across academic research, security advisories, community discussion, and vendor blogs. Each article is scored against a curated keyword list covering prompt injection, SBOM, CI/CD pipeline security, LLM vulnerabilities, container security, and more. High-signal articles are stored in a local SQLite database, optionally summarized using a locally running Ollama model (gemma4 by default), and assembled into a structured Markdown briefing. The briefing includes top highlights with relevance scores, articles grouped by category, a 30-day trend tracker, and a source breakdown table. Everything runs locally — no data leaves your machine.

## Sample Output

Running `python main.py --days 3` produces a file like `briefings/briefing-2026-05-17.md`:

```markdown
# AI & DevSecOps Research Briefing — 2026-05-17

*Generated 2026-05-17 08:14 UTC | 42 relevant articles from the last 3 days*

## Top Highlights

### [Prompt Injection Attacks Against Code Assistants](https://arxiv.org/abs/...)
**Source:** ArXiv CS.CR | **Relevance:** 0.74

Researchers found that popular AI code assistants can be manipulated through
malicious comments in dependencies to generate insecure code. This matters
because developers often trust AI suggestions without reviewing the underlying
training context.

**Topics:** `prompt injection`, `ai code generation security`, `supply chain`

---

## Trending Topics (30-day window)

**Sustained topics** (5+ occurrences):
- `llm security` — seen 14 times
- `software supply chain` — seen 9 times

**Rising topics** (2-4 occurrences):
- `ai soc` — seen 3 times
```

## Usage

**Prerequisites:** Python 3.10+, and [Ollama](https://ollama.com) running locally if you want LLM summaries.

```bash
git clone https://github.com/tdiprima/KoolAdeOps.git
cd KoolAdeOps
pip install -r requirements.txt
```

**Run the full pipeline** (fetch → score → summarize → briefing):

```bash
python main.py
```

**Skip LLM summarization** (useful if Ollama isn't running):

```bash
python main.py --no-llm
```

**Regenerate today's briefing from existing data** (no network calls):

```bash
python main.py --briefing
```

**Set the lookback window** (default is 7 days):

```bash
python main.py --days 3
```

**Export articles for a specific day to a Markdown file:**

```bash
python export_articles.py
```

The script lists the dates available in the database, then prompts you to pick one:

```
Available dates in database:
  2026-05-17
  2026-05-16
  2026-05-15

Enter a date to export (YYYY-MM-DD), 'today' (2026-05-17), or 'yesterday' (2026-05-16).
Date [today]:
```

Press Enter to accept today, type `yesterday`, or enter any `YYYY-MM-DD` date. The output is written to `articles_export_YYYY-MM-DD.md` in the project root.

**Configuration via environment variables:**

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `gemma4` | Local model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint (localhost only) |
| `MAX_ARTICLE_AGE_DAYS` | `7` | Age cutoff for fetched articles |
| `MAX_ARTICLES_PER_FEED` | `20` | Cap per RSS source |
| `FETCH_TIMEOUT` | `30` | HTTP timeout in seconds |

Briefings are written to the `briefings/` directory, named `briefing-YYYY-MM-DD.md`. The SQLite database (`research.db`) accumulates over time, enabling the 30-day trend analysis to improve with each run.
