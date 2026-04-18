import pytest
from unittest.mock import MagicMock
from backend.app.search import min_max_normalize, hybrid_search

def test_min_max_normalize():
    """Test normalization edge cases and standard functionality."""
    assert min_max_normalize([10, 20, 30]) == [0.0, 0.5, 1.0]
    assert min_max_normalize([5, 5, 5]) == [0.5, 0.5, 0.5]
    assert min_max_normalize([100]) == [0.5]
    assert min_max_normalize([]) == []

def test_hybrid_search_alpha_logic():
    """Verify that alpha correctly shifts ranking between BM25 and Vector."""
    bm25 = MagicMock()
    bm25.query.return_value = [{"doc_id": "A", "score": 100.0}]
    
    vector = MagicMock()
    vector.query.return_value = [{"doc_id": "B", "score": 1.0}]
    
    lookup = {
        "A": {"title": "Title A", "text": "Content A"},
        "B": {"title": "Title B", "text": "Content B"}
    }
    
    # Pure BM25
    res_bm25 = hybrid_search("test", 2, 1.0, bm25, vector, lookup)
    assert res_bm25[0]["doc_id"] == "A"
    
    # Pure Vector
    res_vec = hybrid_search("test", 2, 0.0, bm25, vector, lookup)
    assert res_vec[0]["doc_id"] == "B"

def test_hybrid_search_invalid_alpha():
    """Ensure invalid alpha values raise ValueError."""
    with pytest.raises(ValueError):
        hybrid_search("q", 5, 1.5, MagicMock(), MagicMock(), {})
