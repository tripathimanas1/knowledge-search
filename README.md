# Knowledge Search + KPI Dashboard

A hybrid search system combining BM25 lexical retrieval and semantic vector search,
with a KPI dashboard, evaluation harness, and full observability. Runs entirely on CPU.

---

## Architecture

```
data/raw/  ──►  ingest.py  ──►  data/processed/docs.jsonl
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                        bm25_index.py         vector_index.py
                        (rank-bm25)      (sentence-transformers
                              │              + FAISS CPU)
                              └──────────┬──────────┘
                                         ▼
                                     search.py
                                  (hybrid scoring)
                                         │
                                         ▼
                                  FastAPI backend
                                  (routes.py)
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                        SQLite DB            Streamlit UI
                     (query_logs,          (search, KPIs,
                      experiments)          eval, debug)
```

The ingestion pipeline downloads 400 documents from the 20 Newsgroups dataset and
normalizes them into JSONL. The indexing pipeline builds two indexes: a BM25 index
for lexical scoring and a FAISS flat index over sentence-transformer embeddings for
semantic scoring. The FastAPI backend exposes a `/search` endpoint that combines
both scores via a configurable alpha parameter, with per-result score breakdown.
The Streamlit dashboard provides four views: search, KPIs, evaluation trends, and
debug logs. All query logs and experiment metrics are persisted in SQLite.

---

## Quickstart

**Prerequisites**: Python 3.11+, bash (Linux/macOS) or Git Bash (Windows)

```bash
git clone https://github.com/tripathimanas1/knowledge-search.git
cd knowledge-search
./up.sh
```

On first run, `up.sh` will:
1. Create a `.venv` virtual environment
2. Install all dependencies from `requirements.txt`
3. Download and ingest the corpus (~400 docs)
4. Build BM25 and vector indexes (takes ~2 min on first run)
5. Start the backend and dashboard

Once running, open:
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000

---

## Running Tests

```bash
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pytest tests/ -v
```

---

## Running Evaluation

```bash
source .venv/bin/activate
python -m backend.app.eval \
  --queries data/eval/queries.jsonl \
  --qrels data/eval/qrels.json \
  --alpha 0.5
```

To run all 5 experiments (varies alpha from pure BM25 to pure vector):

```bash
python -m backend.app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.0
python -m backend.app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.25
python -m backend.app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.5
python -m backend.app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.75
python -m backend.app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 1.0
```

Results are appended to `data/metrics/experiments.csv` and visualized on the
Evaluation page of the dashboard.

---

## Ingesting Custom Documents

To ingest your own `.txt` or `.md` files instead of the default corpus:

```bash
# Place your files in data/raw/
python -m backend.app.ingest --input data/raw --out data/processed --source folder

# Rebuild indexes
python -m backend.app.index --input data/processed/docs.jsonl
```

---

## SQLite Schema

**`query_logs`** — one row per /search request:

```sql
CREATE TABLE IF NOT EXISTS query_logs (
    request_id  TEXT PRIMARY KEY,
    query       TEXT,
    latency_ms  REAL,
    result_count INTEGER,
    alpha       REAL,
    top_k       INTEGER,
    timestamp   TEXT,
    error       TEXT,
    user_agent  TEXT
);
```

**`experiments`** — one row per eval run:

```sql
CREATE TABLE IF NOT EXISTS experiments (
    run_id      TEXT PRIMARY KEY,
    timestamp   TEXT,
    git_commit  TEXT,
    alpha       REAL,
    model_name  TEXT,
    ndcg_10     REAL,
    recall_10   REAL,
    mrr_10      REAL
);
```

---

## API Reference

**GET /health**
```json
{ "status": "ok", "version": "0.1.0", "commit": "abc1234" }
```

**POST /search**

Request:
```json
{
  "query": "Windows font TrueType",
  "top_k": 10,
  "alpha": 0.5,
  "norm_strategy": "minmax",
  "filters": {}
}
```

Response:
```json
{
  "query": "Windows font TrueType",
  "alpha": 0.5,
  "latency_ms": 42.3,
  "results": [
    {
      "doc_id": "doc_0004",
      "title": "I'm searching for a phonetic TrueType font",
      "text_snippet": "I'm searching for a phonetic TrueType font for Windows 3.1...",
      "bm25_score": 0.87,
      "vector_score": 0.72,
      "hybrid_score": 0.795
    }
  ]
}
```

**GET /metrics** — Prometheus-style plain text:
```
requests_total 142
latency_p50_ms 38.2
latency_p95_ms 91.7
errors_total 0
```

---

## Design Decisions

**Hybrid scoring**: Uses min-max normalization with an epsilon guard to blend BM25
and vector scores. Alpha=0.0 is pure BM25, alpha=1.0 is pure vector. A second
strategy (z-score) is available via the `norm_strategy` parameter. Full rationale
in `docs/decision_log.md`.

**Embedding model**: `all-MiniLM-L6-v2` (22M params, 384-dim) was chosen for fast
CPU inference and good semantic similarity performance at small scale. Full rationale
in `docs/decision_log.md`.

**Stack deviations**: Streamlit was used instead of React+Vite (explicitly allowed
per assignment Section 5). Full justification in `docs/decision_log.md` DL-006.

---

## Docs

- `docs/decision_log.md` — rationale for all key design choices
- `docs/ai_logs.md` — every AI coding assistant prompt mapped to commits
- `docs/break_fix_log.md` — induced failures, observed symptoms, and fixes