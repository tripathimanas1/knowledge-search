import json
from pathlib import Path

def run_eval_setup():
    """Generates templates for evaluation data in data/eval/."""
    docs_path = Path("data/processed/docs.jsonl")
    eval_dir = Path("data/eval")
    
    # Ensure directory exists
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    if not docs_path.exists():
        print(f"CRITICAL ERROR: {docs_path} not found. Please run: python -m backend.app.ingest")
        return
        
    # 1. Print first 50 docs for reference
    print("=========================================")
    print("   SAMPLE CORPUS (FIRST 50 DOCUMENTS)    ")
    print("=========================================")
    try:
        with open(docs_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 50:
                    break
                doc = json.loads(line)
                print(f"{doc['doc_id']} | {doc['title']}")
    except Exception as e:
        print(f"Error reading docs: {e}")
        return

    # 2. Create queries.jsonl (q001 to q025)
    queries_path = eval_dir / "queries.jsonl"
    with open(queries_path, "w", encoding="utf-8") as f:
        for i in range(1, 26):
            q_id = f"q{i:03d}"
            f.write(json.dumps({"query_id": q_id, "query": "FILL IN"}) + "\n")
            
    # 3. Create qrels.json (mapping query_id to list of relevant doc_ids)
    qrels_path = eval_dir / "qrels.json"
    # Using doc_0001 and doc_0002 as placeholders
    qrels_template = {f"q{i:03d}": ["doc_0001", "doc_0002"] for i in range(1, 26)}
    with open(qrels_path, "w", encoding="utf-8") as f:
        json.dump(qrels_template, f, indent=2)
        
    print("\n-----------------------------------------")
    print("SUCCESS: Templates created.")
    print(f"1. Query Template: {queries_path}")
    print(f"2. Relevance Template: {qrels_path}")
    print("-----------------------------------------")
    print("INSTRUCTIONS:")
    print("Edit these files with real queries and relevant doc_ids")
    print("from the printed list above before running evaluation.")
    print("=========================================")

if __name__ == "__main__":
    run_eval_setup()
