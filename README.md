# Knowledge Search + KPI Dashboard

A full-stack hybrid search engine and performance dashboard built for CPU-only environments. This project combines lexical search (BM25) with semantic search (Dense Vectors) to provide high-quality information retrieval from the 20 Newsgroups corpus.

## Architecture

The system follows a modular data pipeline architecture. It starts with an **ingestion** layer that fetches and cleans raw text, followed by an **indexing** phase that generates both a BM25 index and a FAISS-based vector index. 

The **FastAPI backend** serves as the search orchestrator, performing hybrid score fusion (Min-Max normalization) and logging query performance into a SQLite database. Finally, a **Streamlit frontend** provides a searchable UI and a KPI dashboard for monitoring system health and model accuracy.

```text
[Data Ingestion] -> [JSONL Docs] -> [BM25 + FAISS Index]
                                          |
                                          v
[Streamlit UI] <-> [FastAPI Search Service] -> [SQLite Analytics]
```

## Quickstart (1 minute)

```bash
git clone https://github.com/tripathimanas1/knowledge-search
cd knowledge-search
./up.sh
```
Once the bootstrap script finishes, open:
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Dashboard UI**: [http://localhost:8501](http://localhost:8501)

## Running tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Running evaluation

```bash
python -m backend.app.eval --queries data/eval/queries.jsonl \
  --qrels data/eval/qrels.json --alpha 0.5
```

## SQLite schema

```sql
CREATE TABLE query_logs (
    request_id TEXT PRIMARY KEY,
    query TEXT,
    latency_ms REAL,
    result_count INTEGER,
    alpha REAL,
    top_k INTEGER,
    timestamp TEXT,
    error TEXT,
    user_agent TEXT
);

CREATE TABLE experiments (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT,
    git_commit TEXT,
    alpha REAL,
    model_name TEXT,
    ndcg_10 REAL,
    recall_10 REAL,
    mrr_10 REAL
);
```

## Design decisions

**Hybrid Scoring Normalization**: We utilize a Min-Max normalization strategy to bring BM25 scores (unbounded) and Vector scores (0-1 range for cosine) into a shared [0, 1] space. We implemented an `eps` guard (1e-9) in the normalization logic to handle edge cases like flat score distributions (e.g., identical matches), where it defaults to a neutral 0.5 score instead of returning `NaN`.

**Model Choice**: The system uses `all-MiniLM-L6-v2`. With only 22M parameters, it provides an excellent tradeoff between embedding quality and CPU inference speed. It produces 384-dimensional embeddings, keeping the FAISS index compact while ensuring high semantic accuracy. Full decision log available in `docs/decision_log.md`.
