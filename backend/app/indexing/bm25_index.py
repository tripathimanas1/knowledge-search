import pickle
import json
from pathlib import Path
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self, index_dir: str = "data/index/bm25"):
        self.index_dir = Path(index_dir)
        self.index = None
        self.doc_ids = []

    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace-based tokenization with lowercasing."""
        return text.lower().split()

    def build(self, docs: list[dict]) -> None:
        """Constructs and saves the BM25 index from a list of documents."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        corpus = []
        self.doc_ids = []
        
        for doc in docs:
            combined_text = f"{doc.get('title', '')} {doc.get('text', '')}"
            tokens = self._tokenize(combined_text)
            corpus.append(tokens)
            self.doc_ids.append(doc["doc_id"])
            
        self.index = BM25Okapi(corpus)
        
        # Save the rank_bm25 object using pickle protocol 4
        with open(self.index_dir / "index.pkl", "wb") as f:
            pickle.dump(self.index, f, protocol=4)
            
        # Save the ordered doc_ids to maintain mapping between scores and IDs
        with open(self.index_dir / "docids.json", "w") as f:
            json.dump(self.doc_ids, f)

    def load(self) -> None:
        """Loads index and metadata from disk."""
        index_file = self.index_dir / "index.pkl"
        ids_file = self.index_dir / "docids.json"
        
        if index_file.exists() and ids_file.exists():
            with open(index_file, "rb") as f:
                self.index = pickle.load(f)
            with open(ids_file, "r") as f:
                self.doc_ids = json.load(f)
        else:
            self.index = None
            self.doc_ids = []

    def query(self, q: str, top_k: int) -> list[dict]:
        """Computes BM25 scores for a query and returns sorted results."""
        if not self.index or not self.doc_ids:
            return []
            
        tokens = self._tokenize(q)
        scores = self.index.get_scores(tokens)
        
        results = []
        for i, score in enumerate(scores):
            results.append({
                "doc_id": self.doc_ids[i],
                "score": float(score)
            })
            
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
