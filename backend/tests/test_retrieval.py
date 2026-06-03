"""
Test suite for retrieval quality.

HOW DEVELOPERS THINK ABOUT TESTS:
A test has three parts — Arrange, Act, Assert (AAA pattern):
  1. Arrange: set up the data/conditions you need
  2. Act: call the function you're testing
  3. Assert: check that the result is what you expected

Run these tests with: pytest tests/test_retrieval.py -v
The -v flag means "verbose" — show each test name and pass/fail.
"""
import sys
import os

# This adds the backend/ directory to Python's search path
# so we can import our modules like "from utils.embeddings import..."
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embeddings import cosine_similarity, get_embedding
from utils.chroma_store import collection, add_chunks, search, delete_file_chunks


# ─── Unit tests: pure math, no API calls ──────────────────────────────────────

def test_cosine_similarity_identical_vectors():
    """Identical vectors should have similarity of 1.0"""
    vec = [0.1, 0.5, -0.3, 0.8]
    result = cosine_similarity(vec, vec)
    # Use round() because floating point math is never exactly 1.0
    assert round(result, 5) == 1.0, f"Expected 1.0, got {result}"
    print("PASS: identical vectors → similarity 1.0")


def test_cosine_similarity_orthogonal_vectors():
    """Perpendicular vectors (completely unrelated) should be ~0.0"""
    vec_a = [1.0, 0.0]
    vec_b = [0.0, 1.0]
    result = cosine_similarity(vec_a, vec_b)
    assert round(result, 5) == 0.0, f"Expected 0.0, got {result}"
    print("PASS: orthogonal vectors → similarity 0.0")


def test_cosine_similarity_is_symmetric():
    """cosine_similarity(A, B) should equal cosine_similarity(B, A)"""
    vec_a = [0.3, -0.2, 0.8]
    vec_b = [0.1, 0.9, -0.4]
    result_ab = cosine_similarity(vec_a, vec_b)
    result_ba = cosine_similarity(vec_b, vec_a)
    assert round(result_ab, 8) == round(result_ba, 8)
    print("PASS: cosine similarity is symmetric")


# ─── Integration tests: uses ChromaDB (no API calls) ─────────────────────────

TEST_FILENAME = "__test_document__.pdf"

def setup_test_data():
    """Helper: insert fake chunks into ChromaDB for testing"""
    # Clean up any leftover test data from previous runs
    try:
        delete_file_chunks(TEST_FILENAME)
    except:
        pass

    # These are fake but directionally meaningful embeddings.
    # In real usage these come from OpenAI, but for storage tests
    # we just need valid float lists of consistent length.
    fake_chunks = [
        {"chunk_index": 0, "text": "Machine learning is a subset of AI", "char_start": 0, "char_end": 35},
        {"chunk_index": 1, "text": "Python is a programming language", "char_start": 35, "char_end": 67},
        {"chunk_index": 2, "text": "Neural networks process data in layers", "char_start": 67, "char_end": 105},
    ]
    # 8-dim fake embeddings (real ones are 1536-dim, but ChromaDB doesn't care about size)
    fake_embeddings = [
        [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # "ML / AI" direction
        [0.0, 0.0, 0.9, 0.1, 0.0, 0.0, 0.0, 0.0],  # "programming" direction
        [0.8, 0.2, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0],  # also "ML" direction
    ]
    add_chunks(fake_chunks, fake_embeddings, TEST_FILENAME)
    return fake_chunks, fake_embeddings


def test_chunks_stored_and_retrievable():
    """After adding chunks, we should be able to find them by exact query embedding"""
    fake_chunks, fake_embeddings = setup_test_data()

    # Query with the exact embedding of chunk 0 — it should be the top result
    results = search(fake_embeddings[0], top_k=1, filename_filter=TEST_FILENAME)

    assert len(results) == 1
    assert results[0]["text"] == "Machine learning is a subset of AI"
    assert results[0]["similarity_score"] > 0.99  # should be ~1.0 (exact match)
    print(f"PASS: exact embedding retrieves correct chunk (score={results[0]['similarity_score']})")

    # Clean up
    delete_file_chunks(TEST_FILENAME)


def test_metadata_stored_correctly():
    """Metadata like filename and chunk_index should come back intact"""
    fake_chunks, fake_embeddings = setup_test_data()

    results = search(fake_embeddings[1], top_k=1, filename_filter=TEST_FILENAME)

    assert results[0]["metadata"]["filename"] == TEST_FILENAME
    assert results[0]["metadata"]["chunk_index"] == 1
    print("PASS: metadata preserved through storage and retrieval")

    delete_file_chunks(TEST_FILENAME)


def test_top_k_respected():
    """Asking for top_k=2 should return exactly 2 results"""
    fake_chunks, fake_embeddings = setup_test_data()

    results = search(fake_embeddings[0], top_k=2, filename_filter=TEST_FILENAME)
    assert len(results) == 2
    print(f"PASS: top_k=2 returns exactly 2 results")

    delete_file_chunks(TEST_FILENAME)


def test_delete_removes_chunks():
    """After deleting a file's chunks, searching should return 0 results"""
    fake_chunks, fake_embeddings = setup_test_data()
    
    delete_file_chunks(TEST_FILENAME)
    
    # After deletion, ChromaDB might error if the collection is empty and we filter
    # So we check count directly
    count_before_any_docs = collection.count()
    # We just need to verify no TEST_FILENAME chunks remain
    # Try searching and expect empty or non-test results
    results = search(fake_embeddings[0], top_k=3, filename_filter=TEST_FILENAME)
    assert len(results) == 0
    print("PASS: delete_file_chunks removes all chunks for that file")


# Run all tests
if __name__ == "__main__":
    print("\n=== Running unit tests ===")
    test_cosine_similarity_identical_vectors()
    test_cosine_similarity_orthogonal_vectors()
    test_cosine_similarity_is_symmetric()

    print("\n=== Running integration tests ===")
    test_chunks_stored_and_retrievable()
    test_metadata_stored_correctly()
    test_top_k_respected()
    test_delete_removes_chunks()

    print("\nAll tests passed!")