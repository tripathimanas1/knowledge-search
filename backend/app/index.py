import argparse
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

from backend.app.indexing.bm25_index import BM25Index
from backend.app.indexing.vector_index import VectorIndex

def compute_md5(file_path: Path) -> str:
    """Computes the MD5 hash of the given file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def run_indexing(input_path: str):
    """Orchestrates index building and metadata generation."""
    path = Path(input_path)
    if not path.exists():
        print(f"CRITICAL ERROR: Input file '{input_path}' does not exist.")
        exit(1)
        
    # 1. Read processed documents
    docs = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    docs.append(json.loads(line))
    except Exception as e:
        print(f"ERROR: Failed to read {input_path}: {e}")
        exit(1)
            
    if not docs:
        print("ERROR: Corrupt or empty JSONL file. No documents to index.")
        exit(1)
        
    # 2. Initialize indices
    bm25 = BM25Index()
    vector = VectorIndex()
    
    # 3. Build BM25
    print(f"Building BM25 index for {len(docs)} documents...")
    start_bm25 = time.time()
    bm25.build(docs)
    bm25_duration = time.time() - start_bm25
    print(f"-> BM25 completed in {bm25_duration:.2f}s")
    
    # 4. Build Vector
    print(f"Building Vector index (Model: {VectorIndex.MODEL_NAME})...")
    start_vector = time.time()
    vector.build(docs)
    vector_duration = time.time() - start_vector
    print(f"-> Vector completed in {vector_duration:.2f}s")
    
    # 5. Metadata generation
    metadata = {
        "model_name": VectorIndex.MODEL_NAME,
        "embedding_dim": 384,
        "corpus_hash": compute_md5(path),
        "built_at": datetime.now(timezone.utc).isoformat()
    }
    
    meta_path = Path("data/index/metadata.json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"--- Build Complete ---")
    print(f"Metadata saved to: {meta_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Search Indices")
    parser.add_argument("--input", default="data/processed/docs.jsonl", help="Path to processed JSONL")
    args = parser.parse_args()
    
    run_indexing(args.input)
