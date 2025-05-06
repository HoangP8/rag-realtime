#!/bin/bash
# Script to run both the FastAPI service and the worker

# Start the worker in the background
echo "Starting LiveKit Agents worker..."
cd $(dirname $0)/..
python scripts/run_worker.py &
WORKER_PID=$!

# Start the FastAPI service
echo "Starting FastAPI service..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# When the FastAPI service exits, kill the worker
kill $WORKER_PID
