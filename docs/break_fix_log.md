# Break/Fix Log

Documents intentionally induced failures, observed symptoms, and recovery steps.
All three scenarios are covered as required by Section 9 of the assignment.

---

## Scenario A: Semantic Index Mismatch

**What was injected**:
Manually edited `data/index/metadata.json` to set `model_name` to a different model
("all-mpnet-base-v2") and `embedding_dim` to 768, while leaving the actual FAISS
index built with all-MiniLM-L6-v2 (384-dim) in place. Then restarted the backend.

**Observed failure**:
On startup, the API raised a `RuntimeError` before serving any traffic:

```
RuntimeError: Index mismatch: stored model 'all-mpnet-base-v2' dim 768,
current model 'all-MiniLM-L6-v2' dim 384.
Delete data/index/ and re-run index.py.
```

Without the validation, the mismatch would have caused silent incorrect results
or a dimension error during FAISS search.

**Fix implemented**:
`backend/app/startup.py` — `validate_index_metadata()` runs during lifespan startup.
Reads `data/index/metadata.json`, compares stored `model_name` and `embedding_dim`
against current VectorIndex constants. Raises `RuntimeError` with a clear recovery
message if mismatch detected. Raises `FileNotFoundError` if metadata is missing.

**Validated by**:
- `tests/test_scenario_a.py` — asserts RuntimeError is raised on model name mismatch,
  dim mismatch, and FileNotFoundError on missing metadata.
- All tests pass after fix.

---

## Scenario B: Schema Migration Break

**What was injected**:
Manually ran the following SQL against the live database to add a NOT NULL column
without a default value or migration:

```sql
ALTER TABLE query_logs ADD COLUMN session_id TEXT NOT NULL;
```

Then restarted the backend without any migration logic.

**Observed failure**:
Every POST /search request failed with:

```
sqlite3.IntegrityError: NOT NULL constraint failed: query_logs.session_id
```

The dashboard KPI and Debug pages showed no data. New queries were not being logged.

**Fix implemented**:
`backend/app/migrations.py` — implements `get_db_version()` and `run_migrations()`.
Uses SQLite's built-in `PRAGMA user_version` to track schema version.

Migration path:
- v0 → v1: creates initial schema (query_logs, experiments)
- v1 → v2: `ALTER TABLE query_logs ADD COLUMN user_agent TEXT` (nullable, safe default)

`init_db()` in `db.py` calls `run_migrations(conn)` before any other DB operations,
ensuring the schema is always up to date on startup.

**Validated by**:
- `tests/test_migrations.py` — creates a v1 DB manually, runs migrations, asserts
  user_agent column exists and DB version is 2.
- Idempotency test: running migrations twice produces no error.
- All tests pass after fix.

---

## Scenario C: Hybrid Scoring Regression (Divide-by-Zero)

**What was injected**:
Temporarily removed the epsilon guard from `min_max_normalize()`:

```python
# Before fix (broken):
def min_max_normalize(scores):
    min_s, max_s = min(scores), max(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]  # ZeroDivisionError when all equal
```

Then sent a query where all BM25 candidate scores were equal (short single-word query
on a small matching set).

**Observed failure**:
- `ZeroDivisionError` raised inside hybrid_search(), 500 returned from /search.
- When caught silently, NaN values appeared in hybrid_score fields.
- Eval script computed nDCG@10 = 0.0 for all queries using that normalization path.

**Fix implemented**:
`backend/app/search.py` — `min_max_normalize()` restored with epsilon guard:

```python
def min_max_normalize(scores: list[float], eps: float = 1e-9) -> list[float]:
    min_s, max_s = min(scores), max(scores)
    if max_s - min_s < eps:
        return [0.5] * len(scores)  # flat distribution — return neutral score
    return [(s - min_s) / (max_s - min_s + eps) for s in scores]
```

Same guard applied to `z_score_normalize()` — returns `[0.0] * len(scores)` when
standard deviation is below eps.

**Validated by**:
- `tests/test_scenario_c.py` — asserts `min_max_normalize([0.5, 0.5, 0.5])` returns
  `[0.5, 0.5, 0.5]` with no NaN.
- hybrid_search mock test with equal BM25 scores asserts no NaN in any hybrid_score field.
- Re-ran 5 eval experiments after fix — nDCG scores recovered to non-zero values.
- All tests pass after fix.