import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from backend.app.indexing.vector_index import VectorIndex

@pytest.fixture
def mock_docs():
    return [
        {"doc_id": "doc_A", "title": "Alpha", "text": "Information about alpha"},
        {"doc_id": "doc_B", "title": "Beta", "text": "Content regarding beta"}
    ]

def test_vector_index_lifecycle(tmp_path, mock_docs):
    """Test standard build, load, and query cycle for VectorIndex."""
    idx_dir = tmp_path / "vector"
    engine = VectorIndex(index_dir=str(idx_dir))
    
    with patch("backend.app.indexing.vector_index.SentenceTransformer") as mock_st_class:
        mock_model = MagicMock()
        mock_st_class.return_value = mock_model
        
        # Mock 384-dim embeddings
        # doc_A gets [1, 0, 0...], doc_B gets [0, 1, 0...]
        dummy_embeddings = np.zeros((2, 384), dtype="float32")
        dummy_embeddings[0, 0] = 1.0
        dummy_embeddings[1, 1] = 1.0
        mock_model.encode.return_value = dummy_embeddings
        
        # Build index
        engine.build(mock_docs)
        engine.load()
        
        # Mock query embedding closer to doc_A
        query_emb = np.zeros((1, 384), dtype="float32")
        query_emb[0, 0] = 0.9
        query_emb[0, 1] = 0.1
        mock_model.encode.return_value = query_emb
        
        results = engine.query("Find Alpha", top_k=2)
        
        assert len(results) <= 2
        assert results[0]["doc_id"] == "doc_A"
        # Scores should be floats
        assert isinstance(results[0]["score"], float)

def test_vector_index_not_loaded():
    """Verify that query on unitialized index returns empty list."""
    engine = VectorIndex(index_dir="invalid")
    assert engine.query("test", 10) == []
