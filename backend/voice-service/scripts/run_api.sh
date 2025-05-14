#!/bin/bash
# Script to run the FastAPI service 

# Set the working directory to the project root
cd "$(dirname "$0")/.."

echo "Starting FastAPI service..."
uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8003} --reload

