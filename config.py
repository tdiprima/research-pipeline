import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "research.db"
BRIEFINGS_DIR = BASE_DIR / "briefings"


def _parse_int_env(name, default):
    raw = os.environ.get(name, default)
    try:
        value = int(raw)
    except ValueError:
        raise SystemExit(
            f"ERROR: Environment variable {name}='{raw}' is not a valid integer"
        )
    if value <= 0:
        raise SystemExit(
            f"ERROR: Environment variable {name}={value} must be positive"
        )
    return value


def _validate_ollama_url(url):
    parsed = urlparse(url)
    allowed_hosts = ("localhost", "127.0.0.1", "::1")
    if parsed.hostname not in allowed_hosts:
        raise SystemExit(
            f"ERROR: OLLAMA_BASE_URL host '{parsed.hostname}' not in allowed list {allowed_hosts}. "
            f"Only local Ollama instances are supported."
        )
    if parsed.scheme not in ("http", "https"):
        raise SystemExit(
            f"ERROR: OLLAMA_BASE_URL scheme '{parsed.scheme}' invalid. Must be http or https."
        )
    return url.rstrip("/")


OLLAMA_BASE_URL = _validate_ollama_url(
    os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4")

FETCH_TIMEOUT_SECONDS = _parse_int_env("FETCH_TIMEOUT", "30")
MAX_ARTICLE_AGE_DAYS = _parse_int_env("MAX_ARTICLE_AGE_DAYS", "7")
MAX_ARTICLES_PER_FEED = _parse_int_env("MAX_ARTICLES_PER_FEED", "20")
MAX_RESPONSE_BYTES = _parse_int_env("MAX_RESPONSE_BYTES", str(5 * 1024 * 1024))

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
