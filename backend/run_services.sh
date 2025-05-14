#!/bin/bash

# Run all services locally

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: $SCRIPT_DIR"
echo "Current working directory: $(pwd)"

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local service_path="$SCRIPT_DIR/$service_name"
    
    # Special case for voice-service API
    if [ "$service_name" = "voice-service-agent" ]; then
        echo "Starting $service_name..."
        # make the script executable
        chmod +x "voice-service/scripts/run_agent.sh"
        cd "voice-service" && ./scripts/run_agent.sh &
        cd "$SCRIPT_DIR"
    else
        echo "Starting $service_name on port $port..."
        cd "$service_path" && python -m uvicorn app.main:app --host 0.0.0.0 --port $port &
        cd "$SCRIPT_DIR"
    fi
    
    # Wait for service to start
    sleep 2
    echo "$service_name started"
}

# Kill any existing processes
echo "Stopping any existing services..."
pkill -f "uvicorn app.main:app"
pkill -f "python -m agent.worker"
sleep 2

# List directories to verify they exist
# echo "Listing directories in $SCRIPT_DIR:"
# ls -la "$SCRIPT_DIR"

# Start all services
start_service "api-gateway" 8000
start_service "auth-service" 8001
start_service "conversation-service" 8002
start_service "voice-service" 8003
start_service "voice-service-agent" 8003

echo "All services started"
echo "API Gateway: http://localhost:8000/docs"
echo "Auth Service: http://localhost:8001/docs"
echo "Conversation Service: http://localhost:8002/docs"
echo "Voice Service API: http://localhost:8003/docs"
echo "Voice Service Worker: Running in background"

# Wait for user input to stop services
echo "Press Enter to stop all services..."
read

# Kill all services
echo "Stopping all services..."
pkill -f "uvicorn app.main:app"
pkill -f "python -m agent.worker"
echo "All services stopped"
