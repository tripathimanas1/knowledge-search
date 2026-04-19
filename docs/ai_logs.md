# Antigravity Prompt Log

Chronological log of every prompt sent to the AI coding assistant,
what was used from the output, and what was changed manually.
Each entry maps to a git commit.

---

## Entry 001 — Health endpoint

**Task**: Task 1 — scaffold + /health endpoint

**Prompt**:
> In backend/app/api/routes.py implement a FastAPI router with a single
> GET /health endpoint returning { status: "ok", version: "0.1.0",
> commit: <git hash via subprocess, fallback "dev"> }.
> In backend/main.py create the entry point running uvicorn on port 8000.
> No hardcoded paths. No external dependencies beyond fastapi and uvicorn.

**Used from output**: Full routes.py and main.py structure.

**Manual edits**:
- Changed subprocess call to use `check=False` to avoid exception on non-git directories.
- Added `.strip()` to git hash output to remove trailing newline.

**Commit**: b305644

---

## Entry 002 — requirements.txt

**Task**: Task 2

**Prompt**:
> Create requirements.txt with pinned versions for: fastapi, uvicorn,
> rank-bm25, sentence-transformers, faiss-cpu, numpy, streamlit, pytest,
> python-dotenv, pydantic, scikit-learn.
> faiss-cpu not faiss-gpu. All versions pinned explicitly.

**Used from output**: Full requirements.txt.

**Manual edits**:
- Bumped faiss-cpu to verified CPU-only version after testing install.
- Added scikit-learn (needed for 20newsgroups dataset).

**Commit**: e3b693d

---

## Entry 003 — up.sh

**Task**: Task 3

**Prompt**:
> Write up.sh that: creates .venv if missing, activates it, installs
> requirements.txt, checks if data/index/metadata.json exists and if not
> runs ingest then index, starts uvicorn (port 8000) and streamlit
> (port 8501) in background with PIDs saved, prints both URLs,
> traps Ctrl+C to kill both. No absolute paths. Works on Linux and macOS.

**Used from output**: Overall structure and trap logic.

**Manual edits**:
- Added `|| exit 1` after ingest and index commands so script fails loudly on error.
- Changed PID storage to use local variables instead of files.
- Fixed venv activation path compatibility between Linux and macOS.

**Commit**: 6c29e35

---

## Entry 004 — SQLite schema

**Task**: Task 4

**Prompt**:
> In backend/app/db.py implement get_connection(), init_db(), and
> log_query(). Two tables: query_logs and experiments (schemas provided).
> WAL mode. Raw sqlite3, no ORM. init_db() must be idempotent.
> log_query() must never crash the API.
> In tests/test_db.py: test idempotency and insert/retrieve roundtrip
> using tmp_path fixture.

**Used from output**: Full db.py and test structure.

**Manual edits**:
- Wrapped log_query() body in try/except Exception (output only caught sqlite3.Error — too narrow).
- Added `conn.row_factory = sqlite3.Row` to get_connection() for dict-like row access.

**Commit**: a97c05f

---

## Entry 005 — Ingest pipeline

**Task**: Task 5

**Prompt**:
> In backend/app/ingest.py load 20 Newsgroups (first 5 categories,
> train subset, first 400 docs after filtering). Normalize to
> { doc_id, title, text, source, created_at }. Write to
> data/processed/docs.jsonl. Skip docs < 50 chars. Print count.
> CLI: python -m backend.app.ingest --input data/raw --out data/processed.
> Tests in tests/test_ingest.py: test normalization on fake docs,
> test JSONL validity. Do NOT call fetch_20newsgroups in tests.

**Used from output**: Normalization logic and CLI argparse structure.

**Manual edits**:
- Title extraction changed to find first non-empty line (some docs start with blank lines).
- Added .encode('utf-8', errors='replace').decode('utf-8') to handle encoding issues.

**Commit**: e2dd1b4

---

## Entry 006 — BM25 index

**Task**: Task 6

**Prompt**:
> In backend/app/indexing/bm25_index.py implement BM25Index with
> build(), load(), query(). Tokenize title + text. Save/load via pickle
> to data/index/bm25/. Return [{ doc_id, score }] sorted descending.
> Tests in tests/test_bm25.py: 5-doc toy corpus, deterministic ordering,
> empty query no crash.

**Used from output**: Full implementation and tests.

**Manual edits**:
- Added explicit `encoding='utf-8'` to open() calls for JSON files.
- query() was returning np.float64 scores — added `float(s)` cast.

**Commit**: 7f91bfa

---

## Entry 007 — Vector index

**Task**: Task 7

**Prompt**:
> In backend/app/indexing/vector_index.py implement VectorIndex with
> build(), load(), query(). Use all-MiniLM-L6-v2. FAISS IndexFlatIP
> with L2 normalization. CPU only — no device='cuda'. Save index +
> docids. Return [{ doc_id, score }].
> Tests: mock SentenceTransformer, assert correct ranking, no np types
> in output.

**Used from output**: Full implementation.

**Manual edits**:
- Added `device='cpu'` explicitly to SentenceTransformer() constructor.
- FAISS search returns float32 — added `.item()` conversion on scores.
- Fixed test mock: constructed deterministic vectors for correct argmax behavior.

**Commit**: 0a8feba

---

## Entry 008 — Index builder + metadata

**Task**: Task 8

**Prompt**:
> In backend/app/index.py: read docs.jsonl, call BM25Index.build() and
> VectorIndex.build(), compute corpus md5 hash, write
> data/index/metadata.json with model_name, embedding_dim, corpus_hash,
> built_at. Print build times. Fail clearly if docs.jsonl missing.

**Used from output**: Full script.

**Manual edits**:
- md5 was computed on file path string — fixed to read binary and hash actual content.
- Added timing around each index build separately.

**Commit**: 1a81eea

---

## Entry 009 — Hybrid scoring

**Task**: Task 9

**Prompt**:
> In backend/app/search.py implement min_max_normalize() with eps guard
> and hybrid_search() combining BM25 + vector with configurable alpha.
> Fetch top_k*3 candidates from each, union, normalize, combine.
> Return per-result score breakdown. All output scores as Python floats.
> Tests: normalization edge cases, alpha=0.0/1.0 pure ranking tests,
> divide-by-zero test.

**Used from output**: Core logic and most tests.

**Manual edits**:
- Union logic rewrote using explicit dicts keyed by doc_id (set operations lost score mapping).
- text_snippet left as character slice (acceptable for this use case).

**Commit**: f112eb0

---

## Entry 010 — Startup validation

**Task**: Task 10

**Prompt**:
> In backend/app/startup.py implement validate_index_metadata() that
> reads data/index/metadata.json and checks model_name and embedding_dim.
> Raise RuntimeError on mismatch with clear message. Raise
> FileNotFoundError if missing. Tests with tmp_path fixture covering
> all three cases.

**Used from output**: Full implementation and tests.

**Manual edits**: None — output was clean.

**Commit**: 82f57d6

---

## Entry 011 — FastAPI routes (initial)

**Task**: Task 11

**Prompt**:
> In backend/app/api/routes.py add POST /search (Pydantic validation,
> hybrid_search call, log_query, latency measurement) and GET /metrics
> (p50/p95 from SQLite, Prometheus-style text response).
> In backend/main.py use lifespan context manager for startup: init_db,
> validate_index_metadata, load both indexes, load docs_lookup.
> Tests with TestClient: /health, /search valid + invalid bodies, /metrics.

**Used from output**: Route structure, Pydantic model, lifespan pattern.

**Manual edits**:
- docs_lookup loading moved to lifespan so it loads once at startup.
- /metrics returned JSON — added `media_type="text/plain"` to Response.
- Test fixtures rewrote setup to use dependency override.

**Commit**: af6bf82

---

## Entry 012 — Streamlit dashboard

**Task**: Task 12

**Prompt**:
> In frontend/dashboard.py build a 4-page Streamlit app (sidebar nav):
> Search (POST /search, display score cards), KPIs (SQLite metrics,
> charts), Evaluation (experiments.csv table + nDCG line chart),
> Debug Logs (filtered query_logs). Use st.cache_data ttl=30.
> Handle missing data gracefully. Read BACKEND_URL from env.

**Used from output**: Page structure and chart code.

**Manual edits**:
- KPI page crashed on empty DB — added `if df.empty: st.info()` guards.
- Line chart x-axis changed to integer run index for cleaner eval trend.
- Score cards got `round(..., 4)` for display.

**Commit**: fa5b99f

---

## Entry 013 — Eval setup helper

**Task**: Task 13

**Prompt**:
> In backend/app/eval_setup.py: read docs.jsonl, print first 50 doc_ids
> with titles, write template queries.jsonl (25 placeholder entries)
> and qrels.json. Print instructions for manual filling.

**Used from output**: Full script.

**Manual edits**: None.

**Commit**: 113314c

---

## Entry 014 — Metrics implementation

**Task**: Task 14

**Prompt**:
> In backend/app/metrics.py implement dcg_at_k, ndcg_at_k, recall_at_k,
> mrr_at_k as pure functions. Tests covering perfect ranking, reversed
> ranking, partial retrieval, rank-3 first hit, empty list.

**Used from output**: Full implementation and tests.

**Manual edits**:
- IDCG calculation fixed to min(len(relevant), k) for correct ideal ranking.

**Commit**: fa33d89

---

## Entry 015 — Eval harness

**Task**: Task 15

**Prompt**:
> In backend/app/eval.py: read queries.jsonl + qrels.json, POST /search
> per query, compute ndcg_10/recall_10/mrr_10, print per-query + macro
> averages, append to data/metrics/experiments.csv with run metadata.
> CLI: --queries, --qrels, --alpha. Skip failed queries with warning.

**Used from output**: Full script structure.

**Manual edits**:
- CSV append changed from 'w' to 'a' mode with header check.
- Extracted git commit subprocess call to shared backend/app/utils.py.

**Commit**: e9969f7

---

## Entry 016 — Scenario A test

**Task**: Task 16

**Prompt**:
> In tests/test_scenario_a.py write a test that creates fake metadata.json
> with model_name="wrong-model" and embedding_dim=768, calls
> validate_index_metadata(), and asserts RuntimeError is raised with
> message containing "mismatch". Add comment block explaining the scenario
> and fix.

**Used from output**: Full test.

**Manual edits**: None.

**Commit**: bc5e544

---

## Entry 017 — Schema migration + Scenario B

**Task**: Task 17

**Prompt**:
> In backend/app/migrations.py implement PRAGMA user_version based
> migration system: get_db_version(), run_migrations() handling v0->v1
> and v1->v2 (add user_agent column). Update db.py to call
> run_migrations() inside init_db(). Tests: v1 DB migrates to v2,
> idempotency. Append Scenario B entry to docs/break_fix_log.md.

**Used from output**: Migration logic and tests.

**Manual edits**:
- Scenario B migration test needed v1 schema explicitly created before running migrations.

**Commit**: b1afec3

---

## Entry 018 — Scenario C test

**Task**: Task 18

**Prompt**:
> In tests/test_scenario_c.py write tests for flat score divide-by-zero
> case. Assert no NaN in output. Assert all values == 0.5 for flat input.
> Test hybrid_search with equal BM25 scores mock. Append Scenario C entry
> to docs/break_fix_log.md.

**Used from output**: Full test.

**Manual edits**:
- hybrid_search mock updated to return equal scores for ALL docs, not just BM25.

**Commit**: 7d3021e

---

## Entry 019 — README

**Task**: Task 19

**Prompt**:
> Write README.md with sections: Architecture (2 paragraphs + ASCII
> diagram), Quickstart, Running tests, Running evaluation, SQLite schema,
> Design decisions summary. Refer to docs/decision_log.md for full rationale.

**Used from output**: Full README draft.

**Manual edits**:
- Fixed ASCII diagram arrow directions.
- Removed redundant pip install step from quickstart.
- Added correct eval command with module path.

**Commit**: db4c000

---

## Entry 020 — Z-score normalization (Gap fix)

**Task**: Gap 2 — second normalization strategy

**Prompt**:
> In backend/app/search.py add z_score_normalize() with eps guard and
> [-3,3] clipping. Update hybrid_search() to accept norm_strategy param
> ("minmax" or "zscore"). Update POST /search in routes.py to expose
> norm_strategy field. Add tests for z-score normalization edge cases.

**Used from output**: Full implementation.

**Manual edits**:
- z-score clipping replaced np.clip with pure Python min/max to avoid numpy type leakage.

**Commit**: 09e7820

---

## Entry 021 — Folder ingestion + preprocessing tests (Gap fix)

**Task**: Gap 3 — .txt/.md folder ingestion + preprocessing unit tests

**Prompt (folder ingestion)**:
> In backend/app/ingest.py extend to support --source folder mode that
> reads .txt and .md files recursively from --input dir. Skip files
> under 50 chars or over 50KB. Default --source to "newsgroups".
> Tests: 3 tmp .txt files, assert correct JSONL output, small files
> skipped, non-txt/md files ignored.

**Prompt (preprocessing tests)**:
> In backend/tests/test_ingest.py add: test_whitespace_cleanup,
> test_long_doc_truncation (assert len <= 2000), test_short_doc_skipped
> (< 50 chars excluded), test_title_truncation (assert len <= 80).

**Used from output**: Both full implementations.

**Manual edits**:
- Pathlib relative path for source field was absolute on Windows — added .as_posix() relative to repo root.

**Commit**: cfb2167

---

## Entry 022 — Rate limiting + architecture.md (Gap fix)

**Task**: Gap — rate limiting + docs/architecture.md

**Prompt (rate limiting)**:
> In backend/app/api/routes.py add in-memory RateLimiter class using
> collections.deque. 30 requests per 60 seconds per client IP.
> Return 429 on limit exceeded. Only applies to POST /search.
> Test: 31 requests from same IP, assert 31st returns 429.

**Prompt (architecture.md)**:
> Write docs/architecture.md covering: component diagram, data flow
> (ingestion, indexing, search request lifecycle), SQLite schema,
> hybrid scoring formula, directory structure, links to decision_log.

**Used from output**: Both full implementations.

**Manual edits**:
- Rate limiter IP extraction added fallback to "unknown" for test environments where client is None.
- Architecture diagram adjusted arrow directions for accuracy.

**Commit**: b687c3f

---

## Entry 023 — Experiments CSV

**Task**: Task 20 — run 5 alpha experiments

**Action**: Manually ran 5 eval commands with alpha 0.0, 0.25, 0.5, 0.75, 1.0.
Each appended one row to data/metrics/experiments.csv.
No AI assistant prompt used — this was direct CLI execution of the eval harness
built in Entry 015.

**Commit**: 2346bfc