import pytest
import sqlite3
from backend.app.migrations import run_migrations, get_db_version, set_db_version

def test_migration_v0_to_v2(tmp_path):
    """Ensure a fresh DB initializes directly to v2."""
    db_file = tmp_path / "test_mig.db"
    conn = sqlite3.connect(db_file)
    
    run_migrations(conn)
    
    assert get_db_version(conn) == 2
    
    # Check if user_agent column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(query_logs)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "user_agent" in columns
    conn.close()

def test_migration_v1_to_v2(tmp_path):
    """Ensure a v1 DB (no user_agent) is upgraded correctly."""
    db_file = tmp_path / "test_mig_v1.db"
    conn = sqlite3.connect(db_file)
    
    # Manually create V1 state
    conn.execute("CREATE TABLE query_logs (request_id TEXT PRIMARY KEY)")
    set_db_version(conn, 1)
    
    run_migrations(conn)
    
    assert get_db_version(conn) == 2
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(query_logs)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "user_agent" in columns
    conn.close()

def test_migration_idempotency(tmp_path):
    """Ensure running migrations twice does not cause errors or version changes."""
    db_file = tmp_path / "test_mig_idemp.db"
    conn = sqlite3.connect(db_file)
    
    run_migrations(conn)
    run_migrations(conn)
    
    assert get_db_version(conn) == 2
    conn.close()
