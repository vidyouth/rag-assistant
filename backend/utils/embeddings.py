import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
import math

# Load .env file so OPENAI_API_KEY is available
# This looks for .env starting from current directory upward
load_dotenv()

# Create the OpenAI client — it automatically reads OPENAI_API_KEY from environment
client = OpenAI()

def get_embedding(text: str) -> List[float]:
    """
    Converts a string of text into a vector (list of floats).
    
    We use text-embedding-3-small because:
    - It's cheap (very low cost per token)
    - It produces 1536-dimensional vectors
    - It's fast
    - It's accurate enough for most RAG use cases
    """
    # Clean the text — remove excessive newlines which waste tokens
    text = text.replace("\n", " ").strip()
    
    # Call OpenAI's embedding endpoint
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    
    # The response contains a list of embedding objects
    # We only sent one text, so we take index [0]
    # .embedding is the actual list of floats
    return response.data[0].embedding


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Converts multiple texts to embeddings in ONE API call.
    
    Why batch? Because calling the API 50 times for 50 chunks is 
    50x slower and costs more than one call with all 50 texts.
    This is a real-world optimization pattern.
    """
    # Clean all texts
    cleaned = [t.replace("\n", " ").strip() for t in texts]
    
    response = client.embeddings.create(
        input=cleaned,
        model="text-embedding-3-small"
    )
    
    # response.data is a list of EmbeddingObject
    # Each has an .embedding (list of floats) and an .index (which input it came from)
    # Sort by index to preserve original order
    embeddings = sorted(response.data, key=lambda x: x.index)
    return [e.embedding for e in embeddings]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Measures how similar two vectors are using cosine similarity.
    
    The formula: cos(θ) = (A · B) / (|A| × |B|)
    
    Where:
    - A · B  = dot product (sum of element-wise multiplication)
    - |A|    = magnitude of vector A (square root of sum of squares)
    
    Returns a float between -1 and 1:
    - 1.0  = identical direction = same meaning
    - 0.0  = perpendicular = unrelated
    - -1.0 = opposite direction = opposite meaning
    """
    # Dot product: multiply each pair of elements, sum them all
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    
    # Magnitude of each vector
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))
    
    # Avoid division by zero (shouldn't happen with real embeddings)
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    return dot_product / (magnitude_a * magnitude_b)