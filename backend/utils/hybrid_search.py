from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from utils.chroma_store import search, collection
import re


def tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric."""
    return re.findall(r'\b\w+\b', text.lower())


def hybrid_search(
    query: str,
    query_embedding: List[float],
    top_k: int = 5,
    filename_filter: Optional[str] = None,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
) -> List[Dict]:
    """
    Combines vector similarity search (ChromaDB) with BM25 keyword search.

    Why hybrid?
    - Vector search: great at semantic similarity ("what is ML?" finds "machine learning concepts")
    - BM25: great at exact keyword matching ("GPT-4o mini" finds exactly that string)
    - Together: covers both meaning AND exact terms

    Scoring: final_score = (vector_weight × vector_score) + (bm25_weight × bm25_score)
    Both scores are normalized to [0, 1] before combining.
    """
    # --- Step 1: Vector search via ChromaDB ---
    vector_results = search(query_embedding, top_k=top_k * 3, filename_filter=filename_filter)

    if not vector_results:
        return []

    # --- Step 2: BM25 over the same candidate set ---
    texts = [r["text"] for r in vector_results]
    tokenized_corpus = [tokenize(t) for t in texts]
    query_tokens = tokenize(query)

    bm25 = BM25Okapi(tokenized_corpus)
    bm25_raw_scores = bm25.get_scores(query_tokens)

    # Normalize BM25 scores to [0, 1]
    max_bm25 = max(bm25_raw_scores) if max(bm25_raw_scores) > 0 else 1.0
    bm25_scores_normalized = [s / max_bm25 for s in bm25_raw_scores]

    # --- Step 3: Normalize vector scores to [0, 1] ---
    vector_scores = [r["similarity_score"] for r in vector_results]
    max_vec = max(vector_scores) if max(vector_scores) > 0 else 1.0
    vector_scores_normalized = [s / max_vec for s in vector_scores]

    # --- Step 4: Combine scores ---
    combined = []
    for i, result in enumerate(vector_results):
        final_score = (
            vector_weight * vector_scores_normalized[i] +
            bm25_weight * bm25_scores_normalized[i]
        )
        combined.append({
            **result,
            "similarity_score": round(final_score, 4),
            "vector_score": round(vector_scores[i], 4),
            "bm25_score": round(bm25_scores_normalized[i], 4),
        })

    # Sort by combined score, return top_k
    combined.sort(key=lambda x: x["similarity_score"], reverse=True)
    return combined[:top_k]