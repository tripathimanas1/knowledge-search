import pytest
from backend.app.metrics import ndcg_at_k, recall_at_k, mrr_at_k

def test_ndcg_perfect_ranking():
    """Verify that perfect retrieval yields nDCG of 1.0."""
    retrieved = ["doc_1", "doc_2", "doc_3"]
    relevant = {"doc_1", "doc_2"}
    assert ndcg_at_k(retrieved, relevant, k=3) == 1.0

def test_ndcg_reversed_ranking():
    """Verify that lower-ranked relevant docs reduce nDCG."""
    retrieved = ["doc_3", "doc_2", "doc_1"]
    relevant = {"doc_1"}
    # Ideal DCG: 1 / log2(2) = 1.0
    # Actual DCG: 1 / log2(4) = 0.5 (at rank 3)
    assert ndcg_at_k(retrieved, relevant, k=3) == 0.5

def test_recall_at_k():
    """Verify standard recall calculation."""
    relevant = {"doc_A", "doc_B", "doc_C"}
    retrieved = ["doc_A", "doc_X", "doc_Y"]
    assert recall_at_k(retrieved, relevant, k=3) == 1/3

def test_mrr_at_k():
    """Verify reciprocal rank logic."""
    relevant = {"doc_Target"}
    retrieved = ["doc_1", "doc_2", "doc_Target", "doc_4"]
    assert mrr_at_k(retrieved, relevant, k=5) == 1/3
    assert mrr_at_k(retrieved, relevant, k=2) == 0.0

def test_empty_retrieval_safety():
    """Ensure no crashes with empty lists."""
    relevant = {"doc_1"}
    assert ndcg_at_k([], relevant, 10) == 0.0
    assert recall_at_k([], relevant, 10) == 0.0
    assert mrr_at_k([], relevant, 10) == 0.0

def test_no_relevant_docs_safety():
    """Ensure no crashes when the relevant set is empty."""
    assert ndcg_at_k(["doc_1"], set(), 10) == 0.0
    assert recall_at_k(["doc_1"], set(), 10) == 0.0
