#!/bin/bash
# Script to test the Voice Service API

# Set the working directory to the project root
cd "$(dirname "$0")/.."

# Set the API URL
API_URL=${API_URL:-http://localhost:8003}

# Generate a test user ID
USER_ID=$(uuidgen)
echo "Using test user ID: $USER_ID"

# Create a session
echo "Creating a voice session..."
RESPONSE=$(curl -s -X POST \
  "$API_URL/api/v1/voice/session" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_ID" \
  -d '{
    "instructions": "You are a medical assistant. Help the user with their medical questions.",
    "voice_settings": {
      "voice_id": "alloy",
      "temperature": 0.8,
      "max_output_tokens": 2048
    }
  }')

# Extract session ID
SESSION_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION_ID" ]; then
  echo "Failed to create session"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "Created session with ID: $SESSION_ID"

# Get session
echo "Getting session details..."
curl -s -X GET \
  "$API_URL/api/v1/voice/session/$SESSION_ID" \
  -H "Authorization: Bearer $USER_ID" | jq

# Wait for user input
read -p "Press Enter to delete the session..."

# Delete session
echo "Deleting session..."
curl -s -X DELETE \
  "$API_URL/api/v1/voice/session/$SESSION_ID" \
  -H "Authorization: Bearer $USER_ID" | jq

echo "Test completed"
