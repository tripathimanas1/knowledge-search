#!/bin/bash

# Exit immediately if a command exits with a non-zero status during setup
set -e

echo "--- Knowledge Search + KPI Dashboard Setup ---"

# 1. Create .venv if missing
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python -m venv .venv
else
    echo "[1/4] Virtual environment exists."
fi

# 2. Activate .venv
source .venv/Scripts/activate

# 3. Install from requirements.txt
echo "[2/4] Installing requirements..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4. Check if metadata exists, otherwise ingest and index
if [ ! -f "data/index/metadata.json" ]; then
    echo "[3/4] Metadata missing. Initializing data pipeline..."
    
    # Ensure necessary directories exist
    mkdir -p data/processed data/index data/raw
    
    echo "-> Running ingestion..."
    python -m backend.app.ingest --input data/raw --out data/processed || { echo "ERROR: Ingestion failed"; exit 1; }
    
    echo "-> Running indexing..."
    python -m backend.app.index --input data/processed/docs.jsonl || { echo "ERROR: Indexing failed"; exit 1; }
else
    echo "[3/4] Index metadata found. Skipping ingestion/indexing."
fi

# Disable exit on error for process management
set +e

# 5. Start uvicorn backend
echo "[4/4] Starting backend..."
export PYTHONPATH=$PYTHONPATH:.
python -m backend.main &
BACKEND_PID=$!

# 6. Start streamlit frontend
echo "[4/4] Starting dashboard..."
# Running headless for clean logs
streamlit run frontend/dashboard.py --server.port 8501 --server.headless true &
FRONTEND_PID=$!

# 7. Print access points
echo ""
echo "==========================================="
echo "Backend:    http://localhost:8000"
echo "Dashboard:  http://localhost:8501"
echo "==========================================="
echo "Services are running. Press Ctrl+C to stop."

# 8. Trap Ctrl+C and kill both PIDs cleanly
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep the script running to maintain the background processes
wait $BACKEND_PID $FRONTEND_PID
