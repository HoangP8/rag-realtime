#!/bin/bash

# Run all services locally

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    
    # Special case for voice-service which needs both API and worker
    if [ "$service_name" = "voice-service" ]; then
        echo "Starting $service_name on port $port (with worker)..."
        cd $service_name && ./scripts/run.sh &
        cd ..
    else
        echo "Starting $service_name on port $port..."
        cd $service_name && python -m uvicorn app.main:app --host 0.0.0.0 --port $port &
        cd ..
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

# Start all services
start_service "api-gateway" 8000
start_service "auth-service" 8001
start_service "conversation-service" 8002
start_service "voice-service" 8003
start_service "llm-service" 8004

echo "All services started"
echo "API Gateway: http://localhost:8000/docs"
echo "Auth Service: http://localhost:8001/docs"
echo "Conversation Service: http://localhost:8002/docs"
echo "Voice Service: http://localhost:8003/docs"
echo "LLM Service: http://localhost:8004/docs"

# Wait for user input to stop services
echo "Press Enter to stop all services..."
read

# Kill all services
echo "Stopping all services..."
pkill -f "uvicorn app.main:app"
pkill -f "python -m agent.worker"
echo "All services stopped"
