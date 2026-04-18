import sqlite3
import os
from pathlib import Path

from backend.app.migrations import run_migrations

# Relative path from project root
DEFAULT_DB_PATH = Path("data/metrics/app.db")

def get_connection(db_path=None):
    """Returns a sqlite3 connection with Row factory and WAL mode enabled."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db(db_path=None):
    """Idempotently initializes the database schema via migrations."""
    conn = get_connection(db_path)
    run_migrations(conn)
    conn.commit()
    conn.close()

def log_query(record: dict, db_path=None):
    """Inserts a query record into query_logs. Errors are silently swallowed."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_logs (
                request_id, query, latency_ms, result_count, alpha, top_k, timestamp, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get("request_id"),
            record.get("query"),
            record.get("latency_ms"),
            record.get("result_count"),
            record.get("alpha"),
            record.get("top_k"),
            record.get("timestamp"),
            record.get("error")
        ))
        conn.commit()
    except Exception:
        # Silently swallow DB errors to ensure API stability
        pass
    finally:
        if conn:
            conn.close()
