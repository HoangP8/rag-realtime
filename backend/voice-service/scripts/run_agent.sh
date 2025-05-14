#!/bin/bash
# Script to run the LiveKit Agents worker

# Set the working directory to the project root
cd "$(dirname "$0")/.."

echo "Starting LiveKit Agents worker..."
python -m agent.worker dev
