#!/bin/bash
# Script to run the voice service and its dependencies

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker to run RabbitMQ.${NC}"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# Function to check if a port is in use
is_port_in_use() {
    if command -v lsof &> /dev/null; then
        lsof -i:"$1" &> /dev/null
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -tuln | grep ":$1 " &> /dev/null
        return $?
    else
        echo -e "${YELLOW}Warning: Cannot check if port $1 is in use. Please make sure it's available.${NC}"
        return 1
    fi
}

# Start RabbitMQ if not already running
echo -e "${BLUE}Checking if RabbitMQ is running...${NC}"
if ! docker ps | grep -q rabbitmq; then
    echo -e "${YELLOW}RabbitMQ is not running. Starting RabbitMQ container...${NC}"
    
    # Check if port 5672 is in use
    if is_port_in_use 5672; then
        echo -e "${RED}Error: Port 5672 is already in use. Please stop the service using this port.${NC}"
        exit 1
    fi
    
    # Start RabbitMQ container
    docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
    
    # Wait for RabbitMQ to start
    echo -e "${YELLOW}Waiting for RabbitMQ to start...${NC}"
    sleep 10
    
    if ! docker ps | grep -q rabbitmq; then
        echo -e "${RED}Error: Failed to start RabbitMQ container.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}RabbitMQ started successfully!${NC}"
else
    echo -e "${GREEN}RabbitMQ is already running.${NC}"
fi

# Check if voice service port is in use
if is_port_in_use 8003; then
    echo -e "${RED}Error: Port 8003 is already in use. Please stop the service using this port.${NC}"
    exit 1
fi

# Navigate to voice service directory
cd "$(dirname "$0")/voice-service" || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Make test scripts executable
chmod +x scripts/*.py
chmod +x scripts/*.sh

# Start voice service
echo -e "${BLUE}Starting voice service...${NC}"
echo -e "${GREEN}Voice service is running at http://localhost:8003${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the service.${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
