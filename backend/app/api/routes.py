import time
import uuid
import subprocess
from datetime import datetime, timezone
from collections import deque
from fastapi import APIRouter, Request, HTTPException, Response
from pydantic import BaseModel, Field
from backend.app.search import hybrid_search
from backend.app.db import log_query, get_connection

router = APIRouter()

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(10, ge=1, le=50)
    alpha: float = Field(0.5, ge=0.0, le=1.0)
    filters: dict = Field(default_factory=dict)
    norm_strategy: str = "minmax"

class RateLimiter:
    def __init__(self):
        self.clients = {}
        self.max_requests = 30
        self.window_seconds = 60

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        if client_ip not in self.clients:
            self.clients[client_ip] = deque()
            
        q = self.clients[client_ip]
        while q and now - q[0] > self.window_seconds:
            q.popleft()
            
        if len(q) >= self.max_requests:
            return False
            
        q.append(now)
        return True

rate_limiter = RateLimiter()

def get_git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return "dev"

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "commit": get_git_commit()
    }

@router.post("/search")
async def search(request: Request, body: SearchRequest):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded: 30 requests per 60 seconds")

    start_time = time.time()
    req_id = str(uuid.uuid4())
    
    try:
        results = hybrid_search(
            query=body.query,
            top_k=body.top_k,
            alpha=body.alpha,
            bm25_index=request.app.state.bm25_index,
            vector_index=request.app.state.vector_index,
            docs_lookup=request.app.state.docs_lookup,
            norm_strategy=body.norm_strategy
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log to DB
        log_query({
            "request_id": req_id,
            "query": body.query,
            "latency_ms": latency_ms,
            "result_count": len(results),
            "alpha": body.alpha,
            "top_k": body.top_k,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None
        })
        
        return {
            "results": results,
            "latency_ms": latency_ms,
            "query": body.query,
            "alpha": body.alpha
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_query({
            "request_id": req_id,
            "query": body.query,
            "latency_ms": latency_ms,
            "result_count": 0,
            "alpha": body.alpha,
            "top_k": body.top_k,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def metrics():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total requests
    cursor.execute("SELECT COUNT(*) FROM query_logs")
    total_requests = cursor.fetchone()[0]
    
    # Last 1000 rows for percentiles and errors
    cursor.execute("""
        SELECT latency_ms, error FROM query_logs 
        ORDER BY timestamp DESC LIMIT 1000
    """)
    rows = cursor.fetchall()
    conn.close()
    
    latencies = [r["latency_ms"] for r in rows if r["error"] is None]
    error_count = sum(1 for r in rows if r["error"] is not None)
    
    p50, p95 = 0.0, 0.0
    if latencies:
        latencies.sort()
        n = len(latencies)
        p50 = latencies[max(0, int(n * 0.5) - 1)]
        p95 = latencies[max(0, int(n * 0.95) - 1)]
        
    prometheus_data = [
        f"requests_total {total_requests}",
        f"latency_p50_ms {p50:.2f}",
        f"latency_p95_ms {p95:.2f}",
        f"errors_total {error_count}"
    ]
    return Response(content="\n".join(prometheus_data), media_type="text/plain")
