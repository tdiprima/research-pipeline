import json
import logging

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


def check_ollama_available():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        available_names = [m.get("name", "") for m in models]
        model_found = any(OLLAMA_MODEL in name for name in available_names)
        if not model_found:
            logger.warning(
                "Ollama running but model '%s' not found. Available: %s",
                OLLAMA_MODEL,
                available_names,
            )
        return model_found
    except requests.RequestException:
        logger.warning("Ollama not reachable at %s", OLLAMA_BASE_URL)
        return False


def query_ollama(prompt, temperature=0.3):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 512,
        },
    }
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


def summarize_article(article):
    title = article.get("title", "")
    snippet = article.get("content_snippet", "")[:1500]
    source = article.get("source_name", "")

    prompt = f"""You are a research analyst focused on AI and DevSecOps.

Summarize this article in 2-3 concise sentences. Focus on:
- What is new or significant
- Practical implications for DevSecOps practitioners
- Any AI/ML angle if present

Then list 2-5 topic tags (lowercase, short phrases).

Source: {source}
Title: {title}
Content: {snippet}

Respond in this exact JSON format:
{{"summary": "your summary here", "topics": ["topic1", "topic2"]}}

JSON response:"""

    try:
        raw_response = query_ollama(prompt)
        parsed = extract_json_from_response(raw_response)
        if parsed:
            return parsed.get("summary", ""), parsed.get("topics", [])
        logger.warning("Could not parse LLM response for: %s", title)
        return "", []
    except requests.RequestException as exc:
        logger.error("Ollama request failed for '%s': %s", title, exc)
        return "", []


def extract_json_from_response(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def summarize_batch(articles):
    results = []
    for article in articles:
        summary, topics = summarize_article(article)
        results.append({
            "id": article["id"],
            "title": article["title"],
            "summary": summary,
            "topics": topics,
        })
        if summary:
            logger.info("Summarized: %s", article["title"][:80])
        else:
            logger.warning("No summary produced for: %s", article["title"][:80])
    return results
