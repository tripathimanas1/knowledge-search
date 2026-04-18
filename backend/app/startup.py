import json
from pathlib import Path
from backend.app.indexing.vector_index import VectorIndex

def validate_index_metadata(meta_path: str = "data/index/metadata.json") -> None:
    """Validates that the stored index metadata matches the current application configuration."""
    path = Path(meta_path)
    if not path.exists():
        raise FileNotFoundError("Index not found. Run: python -m backend.app.index")
        
    try:
        with open(path, "r") as f:
            meta = json.load(f)
    except json.JSONDecodeError:
        raise RuntimeError(f"Metadata file at {meta_path} is corrupt. Re-run indexing.")
        
    stored_model = meta.get("model_name")
    stored_dim = meta.get("embedding_dim")
    
    current_model = VectorIndex.MODEL_NAME
    current_dim = 384 # Standard for all-MiniLM-L6-v2
    
    if stored_model != current_model or stored_dim != current_dim:
        raise RuntimeError(
            f"Index mismatch: stored model '{stored_model}' dim {stored_dim}, "
            f"current model '{current_model}' dim {current_dim}. "
            "Delete data/index/ and re-run index.py."
        )
