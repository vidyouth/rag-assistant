import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
import json

load_dotenv()
client = OpenAI()

_cache: dict = {}


def rerank_chunks(question: str, chunks: List[Dict], top_n: int = 4) -> List[Dict]:
    """
    Takes candidate chunks from hybrid search and re-scores each one
    specifically for relevance to the question.

    Why this matters:
    - Hybrid search scores measure similarity/keyword overlap
    - But "similar" != "actually answers this question"
    - A reranker asks the LLM directly: "does this chunk help answer X?"
    - Result: fewer but much higher quality chunks sent to the LLM

    We use a single batched LLM call (not one call per chunk) to keep it fast.
    Returns top_n chunks sorted by rerank score, with original scores preserved.
    """
    if not chunks:
        return []

    # If only a few chunks, no point reranking
    if len(chunks) <= top_n:
        return chunks

    # Build a cache key
    cache_key = question.strip().lower() + str([c["metadata"]["chunk_index"] for c in chunks])
    if cache_key in _cache:
        return _cache[cache_key]

    # Build the scoring prompt — one call, all chunks scored together
    chunks_text = ""
    for i, chunk in enumerate(chunks):
        preview = chunk["text"][:300].replace("\n", " ")
        chunks_text += f"\n[{i}] {preview}\n"

    prompt = f"""You are a relevance scoring system. Given a question and a list of document chunks, score each chunk from 0-10 based on how useful it is for answering the question.

Question: {question}

Chunks:
{chunks_text}

Return ONLY a JSON array of scores in order, one integer per chunk.
Example for 3 chunks: [7, 2, 9]
No explanation. Just the JSON array."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()

        # Parse the score array
        # Strip markdown code fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        scores = json.loads(raw)

        if not isinstance(scores, list) or len(scores) != len(chunks):
            return chunks[:top_n]  # fallback

        # Attach rerank scores to each chunk
        scored = []
        for i, chunk in enumerate(chunks):
            rerank_score = float(scores[i]) / 10.0  # normalize to 0-1
            # Blend: 60% rerank, 40% original hybrid score
            blended = round(0.6 * rerank_score + 0.4 * chunk["similarity_score"], 4)
            scored.append({
                **chunk,
                "rerank_score": round(rerank_score, 4),
                "similarity_score": blended,   # overwrite with blended score
            })

        # Sort by blended score, return top_n
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        result = scored[:top_n]
        _cache[cache_key] = result
        return result

    except Exception:
        # Always fall back gracefully — never break the chat
        return chunks[:top_n]