# System Architecture

## Overview

Knowledge Search is a hybrid retrieval system combining BM25 lexical search
and semantic vector search, served via a FastAPI backend and visualized through
a Streamlit dashboard. The entire system runs on CPU and starts with a single
`./up.sh` command.

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        ./up.sh                              │
│  (venv setup → ingest → index → start backend + frontend)  │
└───────────────┬─────────────────────────┬───────────────────┘
                │                         │
                ▼                         ▼
┌──────────────────────┐     ┌─────────────────────────┐
│   FastAPI Backend    │     │   Streamlit Frontend    │
│   (port 8000)        │◄────│   (port 8501)           │
│                      │     │                         │
│  /health             │     │  Search page            │
│  /search             │     │  KPI page               │
│  /metrics            │     │  Evaluation page        │
└──────┬───────────────┘     │  Debug logs page        │
       │                     └─────────────────────────┘
       │
       ├──► search.py (hybrid scoring)
       │         │
       │    ┌────┴─────┐
       │    ▼          ▼
       │  BM25       Vector
       │  Index      Index
       │  (pickle)   (FAISS)
       │
       └──► db.py (SQLite)
                 │
            ┌────┴────┐
            ▼         ▼
       query_logs  experiments
```

---

## Data Flow

### Ingestion + Indexing (run once via up.sh)

```
20 Newsgroups dataset
        │
        ▼
backend/app/ingest.py
  - Fetches 400 docs from sklearn
  - Normalizes: doc_id, title, text, source, created_at
  - Writes: data/processed/docs.jsonl
        │
        ▼
backend/app/index.py
  ┌─────┴──────┐
  ▼            ▼
BM25Index   VectorIndex
  │            │
  │  rank-bm25 │  sentence-transformers
  │  (Okapi)   │  all-MiniLM-L6-v2
  │            │  FAISS IndexFlatIP
  ▼            ▼
data/index/  data/index/
bm25/        vector/
index.pkl    index.faiss
docids.json  docids.json
        │
        ▼
data/index/metadata.json
  { model_name, embedding_dim, corpus_hash, built_at }
```

### Search Request Lifecycle

```
POST /search
  { query, top_k, alpha, norm_strategy, filters }
        │
        ▼
  Rate limiter check (30 req/60s per IP)
        │
        ▼
  hybrid_search()
    ├── BM25Index.query(q, top_k*3)   → [(doc_id, bm25_score)]
    ├── VectorIndex.query(q, top_k*3) → [(doc_id, vector_score)]
    ├── Union of candidate doc_ids
    ├── min_max_normalize() or z_score_normalize()
    └── hybrid = alpha * norm_bm25 + (1-alpha) * norm_vector
        │
        ▼
  log_query() → SQLite query_logs
        │
        ▼
  Response: [{ doc_id, title, text_snippet,
               bm25_score, vector_score, hybrid_score }]
```

---

## SQLite Schema

**query_logs** — one row per /search request:
```sql
CREATE TABLE IF NOT EXISTS query_logs (
    request_id   TEXT PRIMARY KEY,
    query        TEXT,
    latency_ms   REAL,
    result_count INTEGER,
    alpha        REAL,
    top_k        INTEGER,
    timestamp    TEXT,
    error        TEXT,
    user_agent   TEXT
);
```

**experiments** — one row per eval run:
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

## Hybrid Scoring

```
norm_bm25   = min_max_normalize(bm25_scores)
norm_vector = min_max_normalize(vector_scores)

hybrid_score = alpha * norm_bm25 + (1 - alpha) * norm_vector
```

Alpha is a configurable float in [0.0, 1.0]:
- `alpha = 0.0` → pure vector (semantic only)
- `alpha = 0.5` → equal blend (default)
- `alpha = 1.0` → pure BM25 (lexical only)

Two normalization strategies are available: `minmax` (default) and `zscore`.
See `docs/decision_log.md` DL-001 and DL-002 for rationale.

---

## Directory Structure

```
knowledge-search/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py       # FastAPI endpoints + rate limiter
│   │   ├── indexing/
│   │   │   ├── bm25_index.py   # BM25 build/load/query
│   │   │   └── vector_index.py # FAISS build/load/query
│   │   ├── db.py               # SQLite schema + logging
│   │   ├── eval.py             # Evaluation harness
│   │   ├── eval_setup.py       # Eval template generator
│   │   ├── index.py            # Index builder CLI
│   │   ├── ingest.py           # Corpus ingestion CLI
│   │   ├── metrics.py          # nDCG, Recall, MRR
│   │   ├── migrations.py       # SQLite schema migrations
│   │   ├── search.py           # Hybrid scoring logic
│   │   ├── startup.py          # Index validation on startup
│   │   └── utils.py            # Shared helpers (git hash, etc.)
│   ├── main.py                 # FastAPI app entry point
│   └── tests/
│       ├── test_bm25.py
│       ├── test_db.py
│       ├── test_ingest.py
│       ├── test_metrics.py
│       ├── test_migrations.py
│       ├── test_routes.py
│       ├── test_scenario_a.py
│       ├── test_scenario_b.py  (alias: test_migrations.py)
│       ├── test_scenario_c.py
│       ├── test_search.py
│       └── test_startup.py
├── frontend/
│   └── dashboard.py            # Streamlit 4-page dashboard
├── data/
│   ├── raw/                    # Source files (empty; fetched at runtime)
│   ├── processed/              # docs.jsonl (gitignored)
│   ├── index/                  # BM25 + vector artifacts (gitignored)
│   ├── eval/
│   │   ├── queries.jsonl       # 25 labeled queries
│   │   └── qrels.json          # Relevance judgements
│   └── metrics/
│       └── experiments.csv     # Eval run history
├── docs/
│   ├── ai_logs.md            # AI assistant prompt log
│   ├── decision_log.md         # Design decision rationale
│   └── break_fix_log.md        # Induced failure scenarios
├── up.sh                       # One-command setup + run
├── requirements.txt
└── README.md
├── ARCHITECTURE.md         # This file
```

---

## Key Design Decisions

See `docs/decision_log.md` for full rationale on:
- Normalization strategy choice (min-max + z-score)
- Model selection (all-MiniLM-L6-v2)
- FAISS IndexFlatIP over approximate indexes
- SQLite over PostgreSQL
- Streamlit over React+Vite
- Schema migrations via PRAGMA user_version