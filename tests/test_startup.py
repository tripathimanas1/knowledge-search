import pytest
import json
from backend.app.startup import validate_index_metadata
from backend.app.indexing.vector_index import VectorIndex

def test_validate_metadata_success(tmp_path):
    """Ensure validation passes when metadata matches perfectly."""
    meta_file = tmp_path / "metadata.json"
    meta_file.write_text(json.dumps({
        "model_name": VectorIndex.MODEL_NAME,
        "embedding_dim": 384
    }))
    
    # Should not raise any exception
    validate_index_metadata(str(meta_file))

def test_validate_metadata_model_mismatch(tmp_path):
    """Verify RuntimeError when model names differ."""
    meta_file = tmp_path / "metadata.json"
    meta_file.write_text(json.dumps({
        "model_name": "bert-base-uncased",
        "embedding_dim": 384
    }))
    
    with pytest.raises(RuntimeError, match="Index mismatch: stored model 'bert-base-uncased'"):
        validate_index_metadata(str(meta_file))

def test_validate_metadata_dim_mismatch(tmp_path):
    """Verify RuntimeError when embedding dimensions differ."""
    meta_file = tmp_path / "metadata.json"
    meta_file.write_text(json.dumps({
        "model_name": VectorIndex.MODEL_NAME,
        "embedding_dim": 768
    }))
    
    with pytest.raises(RuntimeError, match="dim 768"):
        validate_index_metadata(str(meta_file))

def test_validate_metadata_missing():
    """Verify FileNotFoundError when metadata.json is absent."""
    with pytest.raises(FileNotFoundError, match="Index not found"):
        validate_index_metadata("data/missing_meta.json")
