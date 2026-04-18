import json
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.api.routes import router
from backend.app.startup import validate_index_metadata
from backend.app.db import init_db
from backend.app.indexing.bm25_index import BM25Index
from backend.app.indexing.vector_index import VectorIndex

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB and validate environment
    init_db()
    try:
        validate_index_metadata()
    except Exception as e:
        print(f"Startup Warning: {e}")
        # In a real production app we might exit(1), 
        # but here we'll allow startup to finish so the health check can show issues if needed
        # and to keep dev flow smooth if user hasn't run index.py yet.
    
    # 2. Load Indices
    bm25 = BM25Index()
    bm25.load()
    vector = VectorIndex()
    vector.load()
    
    # 3. Load Document Lookup
    docs_lookup = {}
    docs_path = Path("data/processed/docs.jsonl")
    if docs_path.exists():
        with open(docs_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        doc = json.loads(line)
                        docs_lookup[doc["doc_id"]] = doc
                    except Exception:
                        continue
    
    # 4. Attach to app state for access in routes
    app.state.bm25_index = bm25
    app.state.vector_index = vector
    app.state.docs_lookup = docs_lookup
    
    print("Application startup complete. Indices loaded.")
    yield
    print("Shutting down...")

app = FastAPI(title="Knowledge Search", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
