import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from backend.main import app
from backend.app.api.routes import rate_limiter

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_app_state():
    """Inject mock indices and lookup into the app state for testing."""
    app.state.bm25_index = MagicMock()
    app.state.vector_index = MagicMock()
    app.state.docs_lookup = {"doc_1": {"title": "Test Doc", "text": "Content snippet"}}
    
    # Setup mock behavior for search
    app.state.bm25_index.query.return_value = [{"doc_id": "doc_1", "score": 1.0}]
    app.state.vector_index.query.return_value = [{"doc_id": "doc_1", "score": 0.8}]

def test_health_endpoint():
    """Verify that the health check returns 200 and basic info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "commit" in data

def test_search_valid_request():
    """Test standard hybrid search request."""
    payload = {"query": "test query", "alpha": 0.5, "top_k": 5}
    response = client.post("/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "latency_ms" in data
    assert len(data["results"]) > 0
    assert "hybrid_score" in data["results"][0]

def test_search_invalid_alpha():
    """Verify Pydantic validation for out-of-range alpha."""
    response = client.post("/search", json={"query": "test", "alpha": 1.5})
    assert response.status_code == 422

def test_search_empty_query():
    """Verify Pydantic validation for empty query strings."""
    response = client.post("/search", json={"query": "", "alpha": 0.5})
    assert response.status_code == 422

def test_rate_limiting():
    """Verify that the 31st request from the same IP gets blocked."""
    # Reset state to ensure fresh run if tests run out of order
    rate_limiter.clients.clear()
    
    payload = {"query": "rate limit test", "alpha": 0.5, "top_k": 5}
    
    # 30 requests should succeed
    for _ in range(30):
        response = client.post("/search", json=payload)
        assert response.status_code == 200
        
    # The 31st request should be rejected
    response = client.post("/search", json=payload)
    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded: 30 requests per 60 seconds"
