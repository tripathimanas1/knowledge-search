"""
Scenario A: changing embedding model without rebuilding index.
Fix: startup validation catches dim/model mismatch before serving traffic.
"""

import pytest
import json
from backend.app.startup import validate_index_metadata

def test_index_mismatch_scenario(tmp_path):
    # 1. Create a fake metadata.json with incompatible configuration
    # Current app expects 'all-MiniLM-L6-v2' and 384 dim.
    meta_file = tmp_path / "metadata.json"
    mismatch_data = {
        "model_name": "wrong-model-v2",
        "embedding_dim": 768,
        "corpus_hash": "deadbeef1234",
        "built_at": "2024-01-01T12:00:00Z"
    }
    meta_file.write_text(json.dumps(mismatch_data))
    
    # 2. Call the validation logic
    # 3. Assert that a RuntimeError is raised
    with pytest.raises(RuntimeError) as excinfo:
        validate_index_metadata(str(meta_file))
        
    # 4. Assert error message contains "mismatch" for clear diagnostic
    assert "mismatch" in str(excinfo.value).lower()
