import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "research.db"
BRIEFINGS_DIR = BASE_DIR / "briefings"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4")

FETCH_TIMEOUT_SECONDS = int(os.environ.get("FETCH_TIMEOUT", "30"))
MAX_ARTICLE_AGE_DAYS = int(os.environ.get("MAX_ARTICLE_AGE_DAYS", "7"))
MAX_ARTICLES_PER_FEED = int(os.environ.get("MAX_ARTICLES_PER_FEED", "20"))

RELEVANCE_KEYWORDS = [
    "devsecops", "devops security", "shift left", "sast", "dast", "iast",
    "software supply chain", "sbom", "software bill of materials",
    "cicd security", "ci/cd security", "pipeline security",
    "container security", "kubernetes security", "k8s security",
    "infrastructure as code", "iac security", "terraform security",
    "secret scanning", "secret detection", "credential scanning",
    "dependency scanning", "vulnerability scanning",
    "ai security", "ai vulnerability", "llm security", "llm vulnerability",
    "ai code review", "ai static analysis", "ai penetration testing",
    "machine learning security", "ml security", "adversarial ml",
    "ai soc", "ai threat detection", "ai incident response",
    "ai devsecops", "copilot security", "ai code generation security",
    "prompt injection", "ai supply chain", "model poisoning",
    "security automation", "automated security testing",
    "cloud security", "cloud native security", "zero trust",
    "application security", "appsec",
]

BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
