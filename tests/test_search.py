import pytest
from unittest.mock import MagicMock
from backend.app.search import min_max_normalize, z_score_normalize, hybrid_search

def test_min_max_normalize():
    """Test normalization edge cases and standard functionality."""
    assert min_max_normalize([10, 20, 30]) == [0.0, 0.5, 1.0]
    assert min_max_normalize([5, 5, 5]) == [0.5, 0.5, 0.5]
    assert min_max_normalize([100]) == [0.5]
    assert min_max_normalize([]) == []

def test_z_score_normalize():
    """Test z-score normalization normal logic and flat input."""
    # Flat input
    assert z_score_normalize([5.0, 5.0, 5.0]) == [0.0, 0.0, 0.0]
    
    # Normal input (mean 0, values spread)
    scores = [-1.0, 0.0, 1.0]
    norm = z_score_normalize(scores)
    assert len(norm) == 3
    assert norm[0] < norm[1] < norm[2]
    assert all(-3.0 <= n <= 3.0 for n in norm)

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

def test_hybrid_search_zscore():
    """Test hybrid search with zscore norm strategy."""
    bm25 = MagicMock()
    bm25.query.return_value = [{"doc_id": "A", "score": 100.0}]
    
    vector = MagicMock()
    vector.query.return_value = [{"doc_id": "B", "score": 1.0}]
    
    lookup = {
        "A": {"title": "Title A", "text": "Content A"},
        "B": {"title": "Title B", "text": "Content B"}
    }
    
    res = hybrid_search("test", 2, 0.5, bm25, vector, lookup, norm_strategy="zscore")
    assert len(res) == 2
    assert "A" in [r["doc_id"] for r in res]
    assert "B" in [r["doc_id"] for r in res]
