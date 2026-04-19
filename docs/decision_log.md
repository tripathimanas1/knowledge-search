# Decision Log

This document records key design choices made during development, with rationale.

---

## DL-001 — Hybrid scoring normalization: min-max with epsilon guard

**Decision**: Use min-max normalization with eps=1e-9 as the default strategy.

**Rationale**:
- Min-max is interpretable: output is always in [0, 1], making alpha a meaningful
  linear interpolation parameter between BM25 and vector scores.
- Softmax amplifies score differences exponentially — bad for BM25 where score
  magnitudes vary widely across corpora.
- Rank-based normalization discards score magnitude entirely, losing signal about
  how much better the top result is vs rank 2.
- Epsilon guard (return 0.5 for flat distributions) prevents divide-by-zero when
  all candidates score equally, which happens on short queries with few matching terms.

**Trade-off**: Min-max is sensitive to outliers. A single document with an extremely
high BM25 score can compress all other scores toward 0. Mitigated by fetching
top_k * 3 candidates before merging, which increases score spread.

**Alternatives considered**: softmax (rejected: exponential distortion), reciprocal
rank fusion (rejected: no score magnitude, harder to tune alpha).

---

## DL-002 — Second normalization strategy: z-score

**Decision**: Added z-score normalization as an alternative, exposed via norm_strategy
parameter in /search.

**Rationale**:
- Z-score centers scores around 0 and scales by standard deviation, making it less
  sensitive to outliers than min-max.
- Min-max compresses all scores into [0,1] but a single outlier document can push
  all other scores toward 0.
- Z-score preserves relative spread better on skewed BM25 distributions.

**Trade-off**: Z-score output is unbounded (clipped to [-3, 3] here), making the
alpha blend less intuitive than min-max's [0,1] range. Min-max remains the default
for this reason.

---

## DL-003 — Embedding model: all-MiniLM-L6-v2

**Decision**: Use sentence-transformers/all-MiniLM-L6-v2 as the default embedding model.

**Rationale**:
- 22M parameters — fast CPU inference (~50ms per query on a laptop).
- 384-dimensional embeddings — small FAISS index footprint for 400 docs.
- Strong performance on semantic similarity benchmarks relative to its size.
- Well-maintained, widely used — reduces risk of obscure bugs.

**Trade-off**: Larger models (e.g., all-mpnet-base-v2, 768-dim) give better retrieval
quality but are 3-5x slower on CPU. Not worth it for this scale.

---

## DL-004 — Vector search backend: FAISS IndexFlatIP

**Decision**: Use FAISS IndexFlatIP (exact inner product search) over approximate
methods (IndexHNSW, hnswlib).

**Rationale**:
- Corpus size is ~400 docs. Exact search is fast enough (<5ms).
- Approximate indexes (HNSW) require tuning ef_construction and M parameters —
  adds complexity with no latency benefit at this scale.
- IndexFlatIP with L2-normalized vectors is equivalent to cosine similarity,
  which is correct for sentence-transformer embeddings.

**Trade-off**: Doesn't scale past ~100K docs without moving to an approximate index.
Acceptable for this assignment scope.

---

## DL-005 — Storage: SQLite over PostgreSQL

**Decision**: Use SQLite for query logs and experiment metrics.

**Rationale**:
- No separate process to run — fits the "single ./up.sh" constraint.
- WAL mode enables concurrent reads from Streamlit while FastAPI writes.
- Schema is simple (2 tables, append-only writes). No need for connection pooling
  or advanced query features.

**Trade-off**: Not suitable for multi-instance deployments. Acceptable for a
single-machine assignment.

---

## DL-006 — Frontend: Streamlit over React+Vite

**Decision**: Use Streamlit instead of React+Vite.

**Rationale**:
- Assignment explicitly allows Streamlit as an acceptable alternative.
- Streamlit removes the need for a separate Node.js process, npm install, and
  API client code — reducing up.sh complexity significantly.
- All dashboard requirements (charts, tables, filters, metrics) are natively
  supported by st.metric, st.line_chart, st.dataframe.

**Trade-off**: Less control over UI layout and interactivity vs React. Charts are
less customizable. Acceptable for internal tooling and demo purposes.

---

## DL-007 — BM25 library: rank-bm25

**Decision**: Use rank-bm25 (BM25Okapi) over Whoosh or Elasticsearch.

**Rationale**:
- Pure Python, zero system dependencies — critical for CPU-only reproducibility
  on a fresh machine.
- BM25Okapi is the standard variant with IDF smoothing; good defaults.
- Elasticsearch would require a running JVM — violates the single ./up.sh constraint.

**Trade-off**: No incremental indexing (must rebuild full index on corpus change).
Acceptable for a static corpus.

---

## DL-008 — Schema migrations: PRAGMA user_version

**Decision**: Use SQLite's built-in user_version pragma for migration tracking
instead of Alembic.

**Rationale**:
- Alembic adds ~5 files of boilerplate (env.py, versions/, alembic.ini) for a
  2-table schema — disproportionate complexity.
- user_version is a built-in SQLite integer pragma; no dependencies.
- Migration logic is simple: sequential if/elif version checks in run_migrations().

**Trade-off**: Custom migration system vs battle-tested Alembic. Risk is acceptable
for this schema size. Would switch to Alembic for production.

---

## DL-009 — Corpus: 20 Newsgroups

**Decision**: Use sklearn's 20 Newsgroups dataset (first 5 categories, 400 docs).

**Rationale**:
- Legally redistributable (public domain / open license) — meets Section 6.1 requirement.
- Available via sklearn with no manual download steps — works in up.sh automatically.
- Docs cluster around clear topics (hardware, software, religion, etc.) making it
  easy to write meaningful eval queries and qrels.

**Trade-off**: Corpus is from the early 1990s — some terminology is dated. Not a
concern for demonstrating retrieval quality.

---

## DL-010 — Candidate pool size: top_k * 3

**Decision**: Fetch top_k * 3 candidates from each index before merging for hybrid scoring.

**Rationale**:
- A document may rank highly in one index but not the other. Fetching only top_k
  from each means potentially relevant docs in the union are missed.
- Multiplier of 3 provides enough coverage without excessive computation.
- After merging and re-ranking by hybrid score, final output is trimmed to top_k.

**Trade-off**: 3x more BM25 and vector queries per request. Latency impact is
negligible at this corpus size.