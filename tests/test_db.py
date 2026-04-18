import pytest
import sqlite3
from backend.app.db import init_db, log_query, get_connection

def test_init_db_idempotent(tmp_path):
    """Verify that calling init_db multiple times does not raise errors."""
    db_file = tmp_path / "test_app.db"
    
    # First call
    init_db(db_file)
    
    # Second call (idempotency check)
    init_db(db_file)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    assert "query_logs" in tables
    assert "experiments" in tables

def test_log_query_inserts_and_retrieves(tmp_path):
    """Verify that log_query correctly inserts data into the logs table."""
    db_file = tmp_path / "test_app.db"
    init_db(db_file)
    
    record = {
        "request_id": "req_001",
        "query": "test query",
        "latency_ms": 150.5,
        "result_count": 10,
        "alpha": 0.75,
        "top_k": 5,
        "timestamp": "2026-04-18T20:00:00Z",
        "error": None
    }
    
    log_query(record, db_path=db_file)
    
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM query_logs WHERE request_id = ?", ("req_001",))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row["request_id"] == "req_001"
    assert row["query"] == "test query"
    assert row["latency_ms"] == 150.5
    assert row["alpha"] == 0.75
