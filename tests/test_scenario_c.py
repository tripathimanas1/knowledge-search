"""
Scenario C: divide-by-zero when all BM25 scores are equal.
Fix: eps guard in min_max_normalize returns 0.5 for flat score distributions.
"""

import pytest
import math
from unittest.mock import MagicMock
from backend.app.search import min_max_normalize, hybrid_search

def test_normalization_regression():
    # 1. Test normalization with identical scores
    scores = [0.5, 0.5, 0.5]
    output = min_max_normalize(scores)
    
    # 2 & 3. Assert no NaN and baseline value of 0.5 is returned
    assert all(not math.isnan(s) for s in output)
    assert all(s == 0.5 for s in output)

def test_hybrid_search_flat_scores():
    # 4. Simulate a query where BM25 cannot differentiate documents (all scores equal)
    bm25 = MagicMock()
    bm25.query.return_value = [
        {"doc_id": "doc_1", "score": 10.0},
        {"doc_id": "doc_2", "score": 10.0}
    ]
    
    vector = MagicMock()
    vector.query.return_value = [
        {"doc_id": "doc_1", "score": 0.9},
        {"doc_id": "doc_2", "score": 0.1}
    ]
    
    docs_lookup = {"doc_1": {}, "doc_2": {}}
    
    # 5. Perform hybrid search and ensure no NaN propogates to the final scores
    results = hybrid_search("test", 2, 0.5, bm25, vector, docs_lookup)
    
    for res in results:
        assert not math.isnan(res["hybrid_score"])
        assert isinstance(res["hybrid_score"], float)
