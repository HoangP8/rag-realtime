#!/bin/bash
# Script to run both the FastAPI service and the worker

# Set the working directory to the project root
cd "$(dirname "$0")/.."

# Start the worker in the background
echo "Starting LiveKit Agents worker..."
python -m agent.worker &
WORKER_PID=$!

# Start the FastAPI service
echo "Starting FastAPI service..."
uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8003} --reload

# When the FastAPI service exits, kill the worker
kill $WORKER_PID
