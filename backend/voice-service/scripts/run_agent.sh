#!/bin/bash
# Script to run the LiveKit Agents worker

# Set the working directory to the project root
cd "$(dirname "$0")/.."

# First check if the vectorstore folder faiss exists
cd agent
if [ ! -d "faiss" ]; then
    echo "Vectorstore folder faiss does not exist. Downloading vectorstore..."
    # Make sure the download script is executable
    chmod +x ./scripts/download_vectorstore.sh
    ./scripts/download_vectorstore.sh
fi
cd ..

echo "Starting LiveKit Agents worker..."
python -m agent.worker dev
