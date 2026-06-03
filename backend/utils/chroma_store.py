import chromadb
import os
from typing import List, Dict, Any

# On Render, RENDER=true is set automatically.
# In that environment, use in-memory ChromaDB (ephemeral but functional).
# Locally, use persistent storage as before.
IS_RENDER = os.environ.get("RENDER", "false").lower() == "true"

if IS_RENDER:
    client = chromadb.Client()   # in-memory
else:
    CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)


def add_chunks(chunks: List[Dict], embeddings: List[List[float]], filename: str):
    ids, documents, metadatas = [], [], []
    for chunk, embedding in zip(chunks, embeddings):
        chunk_id = f"{filename}__chunk_{chunk['chunk_index']}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "filename": filename,
            "chunk_index": chunk["chunk_index"],
            "char_start": chunk["char_start"],
            "char_end": chunk["char_end"],
        })
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def search(query_embedding: List[float], top_k: int = 3, filename_filter: str = None) -> List[Dict]:
    where = {"filename": filename_filter} if filename_filter else None
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"]
    }
    if where:
        query_params["where"] = where

    try:
        results = collection.query(**query_params)
    except Exception:
        return []

    formatted = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        similarity = round(1 - distance, 4)
        formatted.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "similarity_score": similarity
        })
    return formatted


def get_store_stats() -> Dict:
    count = collection.count()
    all_items = collection.peek(count if count > 0 else 1)
    filenames = set()
    if all_items["metadatas"]:
        for meta in all_items["metadatas"]:
            filenames.add(meta.get("filename", "unknown"))
    return {"total_chunks": count, "files_indexed": list(filenames)}


def delete_file_chunks(filename: str):
    collection.delete(where={"filename": filename})

def delete_file_chunks(filename: str):
    """
    Removes all chunks belonging to a specific file.
    
    We use ChromaDB's where filter to find all chunks from this file,
    then delete them. This is called when a user deletes a document.
    """
    collection.delete(where={"filename": filename})