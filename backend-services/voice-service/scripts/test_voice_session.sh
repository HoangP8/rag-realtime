#!/bin/bash
# Script to test voice session creation, status, and deletion

# Configuration
API_URL="http://localhost:8000/api/v1"  # Change to your API URL
AUTH_TOKEN="YOUR_AUTH_TOKEN"            # Replace with your auth token

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed. Please install it to parse JSON responses.${NC}"
    echo "On macOS: brew install jq"
    echo "On Ubuntu/Debian: sudo apt-get install jq"
    exit 1
fi

# Function to make API calls
call_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            "${API_URL}${endpoint}"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${API_URL}${endpoint}"
    fi
}

# Create a voice session
echo -e "${BLUE}Creating voice session...${NC}"
response=$(call_api "POST" "/voice/session/create" '{"metadata": {"instructions": "You are a medical assistant. Help the user with their medical questions."}}')

# Check if the response is valid JSON
if ! echo "$response" | jq . > /dev/null 2>&1; then
    echo -e "${RED}Error: Invalid response from server${NC}"
    echo "$response"
    exit 1
fi

# Extract session ID
session_id=$(echo "$response" | jq -r '.id')
token=$(echo "$response" | jq -r '.token')

if [ "$session_id" == "null" ] || [ -z "$session_id" ]; then
    echo -e "${RED}Error: Failed to create session${NC}"
    echo "$response"
    exit 1
fi

echo -e "${GREEN}Session created successfully!${NC}"
echo -e "Session ID: ${YELLOW}$session_id${NC}"
echo -e "Token: ${YELLOW}$token${NC}"

# Get session status
echo -e "\n${BLUE}Getting session status...${NC}"
status_response=$(call_api "GET" "/voice/session/$session_id/status")

echo -e "${GREEN}Session status:${NC}"
echo "$status_response" | jq .

# Ask user if they want to delete the session
read -p "Do you want to delete the session? (y/n): " delete_choice

if [ "$delete_choice" == "y" ] || [ "$delete_choice" == "Y" ]; then
    echo -e "\n${BLUE}Deleting session...${NC}"
    delete_response=$(call_api "DELETE" "/voice/session/$session_id")
    
    if [ -z "$delete_response" ]; then
        echo -e "${GREEN}Session deleted successfully!${NC}"
    else
        echo -e "${RED}Error deleting session:${NC}"
        echo "$delete_response"
    fi
else
    echo -e "\n${YELLOW}Session not deleted. You can use this session ID for WebSocket testing.${NC}"
    echo -e "Session ID: ${YELLOW}$session_id${NC}"
    echo -e "Token: ${YELLOW}$token${NC}"
fi

echo -e "\n${GREEN}Test completed!${NC}"
