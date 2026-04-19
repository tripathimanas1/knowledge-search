import math

def min_max_normalize(scores: list[float], eps: float = 1e-9) -> list[float]:
    """Normalizes a list of scores to the range [0, 1]."""
    if not scores:
        return []
    
    if len(scores) == 1:
        return [0.5]
        
    s_min = min(scores)
    s_max = max(scores)
    diff = s_max - s_min
    
    if diff < eps:
        # Avoid divide-by-zero if all scores are identical
        return [0.5] * len(scores)
        
    return [(s - s_min) / diff for s in scores]

def z_score_normalize(scores: list[float], eps: float = 1e-9) -> list[float]:
    """Normalizes a list of scores using Z-score and clips to [-3, 3]."""
    if not scores:
        return []
    
    n = len(scores)
    mean = sum(scores) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in scores) / n)
    
    if std < eps:
        return [0.0] * n
        
    normalized = [(s - mean) / (std + eps) for s in scores]
    return [max(-3.0, min(3.0, s)) for s in normalized]

def hybrid_search(
    query: str,
    top_k: int,
    alpha: float,
    bm25_index,
    vector_index,
    docs_lookup: dict[str, dict],
    norm_strategy: str = "minmax"
) -> list[dict]:
    """Combines BM25 and Vector search results using min-max normalization."""
    
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha must be a float between 0.0 and 1.0")
        
    # Fetch candidates (broadening the pool)
    candidates_count = top_k * 3
    bm25_results = bm25_index.query(query, candidates_count)
    vector_results = vector_index.query(query, candidates_count)
    
    # Create doc_id -> score maps
    bm25_map = {r["doc_id"]: r["score"] for r in bm25_results}
    vector_map = {r["doc_id"]: r["score"] for r in vector_results}
    
    # Union of all candidate IDs
    union_ids = list(set(bm25_map.keys()) | set(vector_map.keys()))
    
    if not union_ids:
        return []
        
    # Extract raw scores for the union set
    raw_bm25 = [bm25_map.get(doc_id, 0.0) for doc_id in union_ids]
    raw_vector = [vector_map.get(doc_id, 0.0) for doc_id in union_ids]
    
    # Normalize scores
    if norm_strategy == "zscore":
        norm_bm25 = z_score_normalize(raw_bm25)
        norm_vector = z_score_normalize(raw_vector)
    else:
        norm_bm25 = min_max_normalize(raw_bm25)
        norm_vector = min_max_normalize(raw_vector)
    
    scored_results = []
    for i, doc_id in enumerate(union_ids):
        doc = docs_lookup.get(doc_id, {})
        
        # Calculate hybrid score
        hybrid_score = alpha * norm_bm25[i] + (1 - alpha) * norm_vector[i]
        
        scored_results.append({
            "doc_id": doc_id,
            "title": doc.get("title", "Untitled"),
            "text_snippet": doc.get("text", "")[:200],
            "bm25_score": float(raw_bm25[i]),
            "vector_score": float(raw_vector[i]),
            "hybrid_score": float(hybrid_score)
        })
        
    # Sort and return top k
    scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return scored_results[:top_k]
