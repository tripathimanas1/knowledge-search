import math

def dcg_at_k(relevances: list[int], k: int) -> float:
    """Calculates Discounted Cumulative Gain at K."""
    relevances = relevances[:k]
    score = 0.0
    for i, rel in enumerate(relevances):
        # Discounting starts from rank 1 (index 0)
        # formula: rel_i / log2(rank + 1) -> log2(i + 2)
        score += rel / math.log2(i + 2)
    return score

def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Calculates Normalized Discounted Cumulative Gain at K."""
    if not relevant:
        return 0.0
    
    # 1. Actual DCG
    actual_relevances = [1 if doc_id in relevant else 0 for doc_id in retrieved[:k]]
    actual_dcg = dcg_at_k(actual_relevances, k)
    
    # 2. Perfect DCG (all relevant docs at the top)
    ideal_count = min(len(relevant), k)
    ideal_relevances = [1] * ideal_count + [0] * (k - ideal_count)
    idcg = dcg_at_k(ideal_relevances, k)
    
    if idcg == 0:
        return 0.0
        
    return actual_dcg / idcg

def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Calculates Recall at K (proportion of relevant documents retrieved)."""
    if not relevant:
        return 0.0
    
    top_k_retrieved = set(retrieved[:k])
    intersection = top_k_retrieved & relevant
    return len(intersection) / len(relevant)

def mrr_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Calculates Mean Reciprocal Rank at K."""
    for i, doc_id in enumerate(retrieved[:k]):
        if doc_id in relevant:
            return 1.0 / (i + 1)
            
    return 0.0
