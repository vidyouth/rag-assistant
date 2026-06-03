import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

_cache: dict = {}


def rewrite_query(raw_query: str) -> str:
    """
    Uses a cheap, fast LLM call to:
    1. Fix spelling mistakes ("teach em" → "teach me")
    2. Expand abbreviations and informal phrasing
    3. Make the query more semantically rich for embedding

    Results are cached so the same query never costs twice.
    This uses gpt-4o-mini with max_tokens=60 — costs a fraction of a cent.
    """
    if not raw_query or len(raw_query.strip()) < 3:
        return raw_query

    normalized = raw_query.strip().lower()
    if normalized in _cache:
        return _cache[normalized]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=80,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a search query optimizer. Given a user's raw query (which may contain "
                        "typos, informal language, or abbreviations), rewrite it as a clean, well-formed "
                        "search query that preserves the original intent. "
                        "Fix spelling. Expand abbreviations. Make it specific. "
                        "Return ONLY the rewritten query — no explanation, no quotes, no punctuation changes."
                    )
                },
                {"role": "user", "content": raw_query}
            ]
        )
        rewritten = response.choices[0].message.content.strip()
        # Sanity check: if the rewrite is way longer, something went wrong
        if len(rewritten) > len(raw_query) * 4:
            return raw_query
        _cache[normalized] = rewritten
        return rewritten
    except Exception:
        return raw_query   # always fall back gracefully