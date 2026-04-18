import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

class VectorIndex:
    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self, index_dir: str = "data/index/vector"):
        self.index_dir = Path(index_dir)
        self.index = None
        self.doc_ids = []
        self.model = None

    def _get_model(self):
        """Lazy-load the SentenceTransformer model on CPU."""
        if self.model is None:
            self.model = SentenceTransformer(self.MODEL_NAME, device="cpu")
        return self.model

    def build(self, docs: list[dict]) -> None:
        """Embeds documents and builds a FAISS index with L2-normalized inner product."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        model = self._get_model()
        
        texts = [f"{doc.get('title', '')} {doc.get('text', '')}" for doc in docs]
        self.doc_ids = [doc["doc_id"] for doc in docs]
        
        # Embed text
        embeddings = model.encode(
            texts, 
            batch_size=32, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)
        
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        
        faiss.write_index(self.index, str(self.index_dir / "index.faiss"))
        with open(self.index_dir / "docids.json", "w") as f:
            json.dump(self.doc_ids, f)

    def load(self) -> None:
        """Loads FAISS index and document metadata."""
        index_path = self.index_dir / "index.faiss"
        ids_path = self.index_dir / "docids.json"
        
        if index_path.exists() and ids_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(ids_path, "r") as f:
                self.doc_ids = json.load(f)
            self._get_model() 
        else:
            self.index = None
            self.doc_ids = []

    def query(self, q: str, top_k: int) -> list[dict]:
        """Embeds query and searches the FAISS index."""
        if self.index is None or self.model is None:
            return []
            
        q_emb = self.model.encode([q], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(q_emb)
        
        scores, indices = self.index.search(q_emb, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1: 
                continue
            results.append({
                "doc_id": self.doc_ids[idx],
                "score": float(score)
            })
            
        return results
