from typing import List, Dict, Any
from utils.embeddings import cosine_similarity

# This is our "vector store" — just a Python list of dicts
# Each dict has: text, embedding, and metadata
# Think of this like a simple database table
_store: List[Dict[str, Any]] = []


def add_chunks(chunks: List[Dict], embeddings: List[List[float]], filename: str):
    """
    Stores chunks + their embeddings together.
    
    chunks: list of dicts from your pdf_parser (has 'text', 'chunk_index', etc.)
    embeddings: list of vectors — one per chunk, same order
    filename: which PDF these came from
    """
    for chunk, embedding in zip(chunks, embeddings):
        _store.append({
            "text": chunk["text"],
            "embedding": embedding,
            "metadata": {
                "filename": filename,
                "chunk_index": chunk["chunk_index"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
            }
        })


def search(query_embedding: List[float], top_k: int = 3) -> List[Dict]:
    """
    Finds the top_k most relevant chunks for a given query embedding.
    
    Steps:
    1. Compare query embedding to EVERY stored embedding
    2. Score each one using cosine similarity
    3. Sort by score (highest = most relevant)
    4. Return top_k results
    
    This is the core of semantic search.
    """
    if not _store:
        return []
    
    # Score every stored chunk against the query
    scored = []
    for item in _store:
        score = cosine_similarity(query_embedding, item["embedding"])
        scored.append({
            "text": item["text"],
            "metadata": item["metadata"],
            "similarity_score": round(score, 4)
        })
    
    # Sort by score descending — best match first
    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    # Return only the top k results
    return scored[:top_k]


def get_store_stats() -> Dict:
    """Useful for debugging — tells you what's in the store."""
    return {
        "total_chunks": len(_store),
        "files_indexed": list(set(
            item["metadata"]["filename"] for item in _store
        ))
    }


def clear_store():
    """Removes everything from memory. Useful for testing."""
    _store.clear()