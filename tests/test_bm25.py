import pytest
from backend.app.indexing.bm25_index import BM25Index

@pytest.fixture
def toy_corpus():
    return [
        {"doc_id": "doc_1", "title": "Python Programming", "text": "I love coding in Python for data science."},
        {"doc_id": "doc_2", "title": "Healthy Diets", "text": "Eating vegetables and fruits is good for health."},
        {"doc_id": "doc_3", "title": "Deep Learning", "text": "Neural networks are a key part of deep learning."},
        {"doc_id": "doc_4", "title": "Weather Report", "text": "The sky is blue and it is sunny today."},
        {"doc_id": "doc_5", "title": "FastAPI Web", "text": "FastAPI is a modern web framework for Python."}
    ]

def test_bm25_build_and_query(tmp_path, toy_corpus):
    """Test standard build, load, and query cycle."""
    idx_dir = tmp_path / "bm25"
    engine = BM25Index(index_dir=str(idx_dir))
    
    engine.build(toy_corpus)
    engine.load()
    
    # Query for "Python" should return Python docs (1 and 5)
    results = engine.query("Python", top_k=2)
    assert len(results) == 2
    returned_ids = {r["doc_id"] for r in results}
    assert "doc_1" in returned_ids or "doc_5" in returned_ids
    
    # Test sorting
    assert results[0]["score"] >= results[1]["score"]

def test_bm25_empty_query(tmp_path, toy_corpus):
    """Verify empty query returns results without error."""
    idx_dir = tmp_path / "bm25"
    engine = BM25Index(index_dir=str(idx_dir))
    engine.build(toy_corpus)
    
    results = engine.query("", top_k=5)
    assert isinstance(results, list)
    assert len(results) == 5

def test_bm25_not_loaded():
    """Verify query on unitialized index returns empty list."""
    engine = BM25Index(index_dir="non_existent")
    results = engine.query("test", top_k=10)
    assert results == []
