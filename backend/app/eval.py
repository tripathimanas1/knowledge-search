import argparse
import json
import requests
import os
import csv
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from backend.app.metrics import ndcg_at_k, recall_at_k, mrr_at_k

# Environment Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def get_git_commit():
    """Retrieves the current git commit hash via subprocess."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode('ascii')
    except Exception:
        return "dev"

def run_evaluation(queries_path: str, qrels_path: str, alpha: float):
    """Executes evaluation across all queries and logs results."""
    
    # 1. Load Queries
    queries = []
    if not Path(queries_path).exists():
        print(f"Error: {queries_path} not found.")
        return
        
    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
            
    # 2. Load Ground Truth (qrels)
    if not Path(qrels_path).exists():
        print(f"Error: {qrels_path} not found.")
        return
        
    with open(qrels_path, "r", encoding="utf-8") as f:
        qrels = json.load(f)
        
    scores_list = []
    print(f"Starting evaluation (alpha={alpha}) via {BACKEND_URL}...")
    
    for q in queries:
        q_id = q["query_id"]
        q_text = q["query"]
        relevant_set = set(qrels.get(q_id, []))
        
        if not relevant_set:
            print(f"-> Skipping {q_id}: No ground truth docs found in qrels.")
            continue
            
        try:
            # Call backend API
            resp = requests.post(f"{BACKEND_URL}/search", json={
                "query": q_text,
                "alpha": float(alpha),
                "top_k": 10
            }, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            retrieved_ids = [r["doc_id"] for r in data["results"]]
            
            # Compute Metrics
            n10 = ndcg_at_k(retrieved_ids, relevant_set, 10)
            r10 = recall_at_k(retrieved_ids, relevant_set, 10)
            m10 = mrr_at_k(retrieved_ids, relevant_set, 10)
            
            scores_list.append({"n10": n10, "r10": r10, "m10": m10})
            print(f"Q: {q_id} | nDCG@10: {n10:.3f} | Recall@10: {r10:.3f} | MRR@10: {m10:.3f}")
            
        except Exception as e:
            print(f"Warning: Failed to evaluate query {q_id}: {e}")
            
    if not scores_list:
        print("CRITICAL: No queries were successfully evaluated.")
        return
        
    # 3. Compute Macro Averages
    count = len(scores_list)
    avg_n10 = sum(s["n10"] for s in scores_list) / count
    avg_r10 = sum(s["r10"] for s in scores_list) / count
    avg_m10 = sum(s["m10"] for s in scores_list) / count
    
    print("\n" + "="*40)
    print("MACRO AVERAGES")
    print("="*40)
    print(f"nDCG@10:   {avg_n10:.4f}")
    print(f"Recall@10: {avg_r10:.4f}")
    print(f"MRR@10:    {avg_m10:.4f}")
    print("="*40)
    
    # 4. Save to Experiments CSV
    metrics_path = Path("data/metrics/experiments.csv")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    header = ["run_id", "timestamp", "git_commit", "alpha", "model_name", "ndcg_10", "recall_10", "mrr_10"]
    file_exists = metrics_path.exists()
    
    with open(metrics_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
            
        writer.writerow([
            f"run_{int(time.time())}",
            datetime.now(timezone.utc).isoformat(),
            get_git_commit(),
            alpha,
            "all-MiniLM-L6-v2",
            round(avg_n10, 4),
            round(avg_r10, 4),
            round(avg_m10, 4)
        ])
        
    print(f"Summary logged to {metrics_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search Evaluation Harness")
    parser.add_argument("--queries", default="data/eval/queries.jsonl", help="Path to queries")
    parser.add_argument("--qrels", default="data/eval/qrels.json", help="Path to relevance labels")
    parser.add_argument("--alpha", type=float, default=0.5, help="Hybrid alpha value")
    args = parser.parse_args()
    
    run_evaluation(args.queries, args.qrels, args.alpha)
