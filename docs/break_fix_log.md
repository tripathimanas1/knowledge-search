# Knowledge Search Break/Fix Log

## Scenario A: Index model mismatch
**Injected**: Updated `VectorIndex.MODEL_NAME` to a 768-dim model but served a 384-dim index.
**Observed**: Retrieval failed with FAISS dimensionality errors.
**Fix**: Implemented `validate_index_metadata()` in `startup.py` to compare disk metadata with runtime config.
**Validated**: `tests/test_scenario_a.py` confirms process halts before serving traffic.

## Scenario B: Schema migration break
**Injected**: Added NOT NULL column to `query_logs` without migration.
**Observed**: INSERT failed with "NOT NULL constraint", dashboard showed no data.
**Fix**: Implemented `run_migrations()` with version tracking via `PRAGMA user_version` in `migrations.py`.
**Validated**: `tests/test_migrations.py` confirms old DBs migrate cleanly to include the new column.
