import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from sklearn.datasets import fetch_20newsgroups

def clean_text(text: str) -> str:
    """Normalize whitespace and truncate text."""
    # Replace any sequence of whitespace with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:2000]

def normalize_doc(i: int, raw_text: str) -> dict:
    """Transform raw text into the required document schema."""
    cleaned = clean_text(raw_text)
    
    # Skip if document is too short
    if len(cleaned) < 50:
        return None
    
    # Extract title: first non-empty line
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    title = lines[0][:80] if lines else "Untitled"
    
    return {
        "doc_id": f"doc_{i:04d}",
        "title": title,
        "text": cleaned,
        "source": "20newsgroups",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

def run_ingest(output_dir: str):
    """Fetch 20 Newsgroups data and save as JSONL."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "docs.jsonl"
    
    # Get standard target names to select first 5
    temp_dataset = fetch_20newsgroups(subset='train')
    target_categories = temp_dataset.target_names[:5]
    
    print(f"Fetching categories: {target_categories}")
    data = fetch_20newsgroups(
        subset='train',
        categories=target_categories,
        remove=('headers', 'footers', 'quotes')
    )
    
    docs = []
    processed_count = 0
    for raw_text in data.data:
        if processed_count >= 400:
            break
            
        doc = normalize_doc(processed_count, raw_text)
        if doc:
            docs.append(doc)
            processed_count += 1
            
    # Write to JSONL
    with open(out_path, 'w', encoding='utf-8') as f:
        for doc in docs:
            f.write(json.dumps(doc) + '\n')
            
    print(f"Ingested {len(docs)} documents to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest 20 Newsgroups corpus.")
    parser.add_argument("--input", default="data/raw", help="Input directory (unused for this downloader)")
    parser.add_argument("--out", default="data/processed", help="Output directory for processed documents")
    args = parser.parse_args()
    
    run_ingest(args.out)
