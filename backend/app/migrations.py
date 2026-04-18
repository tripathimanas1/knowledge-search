import sqlite3

SCHEMA_VERSION = 2

def get_db_version(conn):
    """Reads the current user_version from SQLite pragma."""
    return conn.execute("PRAGMA user_version").fetchone()[0]

def set_db_version(conn, version):
    """Sets the user_version pragma."""
    conn.execute(f"PRAGMA user_version = {version}")

def run_migrations(conn):
    """Progressively applies schema changes based on the current version."""
    version = get_db_version(conn)
    cursor = conn.cursor()
    
    # Version 0: Fresh Database
    if version == 0:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                request_id TEXT PRIMARY KEY,
                query TEXT,
                latency_ms REAL,
                result_count INTEGER,
                alpha REAL,
                top_k INTEGER,
                timestamp TEXT,
                error TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                run_id TEXT PRIMARY KEY,
                timestamp TEXT,
                git_commit TEXT,
                alpha REAL,
                model_name TEXT,
                ndcg_10 REAL,
                recall_10 REAL,
                mrr_10 REAL
            )
        """)
        version = 1
        set_db_version(conn, 1)

    # Version 1 -> 2: Add user_agent field
    if version == 1:
        try:
            cursor.execute("ALTER TABLE query_logs ADD COLUMN user_agent TEXT")
        except sqlite3.OperationalError:
            # Column may physically exist due to failed/manual attempts
            pass
        set_db_version(conn, 2)
