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

def run_folder_ingest(input_dir: str, output_dir: str):
    """Read .txt and .md files from input_dir and save as JSONL."""
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "docs.jsonl"
    repo_root = Path.cwd()
    
    docs = []
    processed_count = 0
    
    if in_dir.exists():
        for file_path in in_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".txt", ".md"]:
                # skip if larger than 50KB
                if file_path.stat().st_size > 50 * 1024:
                    continue
                
                try:
                    raw_text = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                
                cleaned = clean_text(raw_text)
                if len(cleaned) < 50:
                    continue
                
                title = file_path.stem[:80]
                
                try:
                    source = str(file_path.relative_to(repo_root))
                except ValueError:
                    source = str(file_path)
                    
                # Use st_mtime for file modification time
                created_at = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
                
                doc = {
                    "doc_id": f"doc_{processed_count:04d}",
                    "title": title,
                    "text": cleaned,
                    "source": source,
                    "created_at": created_at
                }
                docs.append(doc)
                processed_count += 1

    with open(out_path, 'w', encoding='utf-8') as f:
        for doc in docs:
            f.write(json.dumps(doc) + '\n')
            
    print(f"Ingested {len(docs)} folder documents to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest 20 Newsgroups or folder corpus.")
    parser.add_argument("--input", default="data/raw", help="Input directory")
    parser.add_argument("--out", default="data/processed", help="Output directory for processed documents")
    parser.add_argument("--source", default="newsgroups", choices=["newsgroups", "folder"], help="Source mode")
    args = parser.parse_args()
    
    if args.source == "newsgroups":
        run_ingest(args.out)
    elif args.source == "folder":
        run_folder_ingest(args.input, args.out)
