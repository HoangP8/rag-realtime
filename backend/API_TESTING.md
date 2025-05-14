# API Testing Guide for Medical Chatbot Backend

This guide provides instructions for testing the API endpoints of the Medical Chatbot backend.

## Table of Contents

1. [Using Swagger UI](#using-swagger-ui)
2. [Using the Test Script](#using-the-test-script)
3. [Manual Testing with curl](#manual-testing-with-curl)
4. [Troubleshooting](#troubleshooting)

## Using Swagger UI

FastAPI provides built-in API documentation and testing capabilities through Swagger UI.

### 1. Start the Services

First, start the services you want to test:

```bash
# Start all services using the combined service runner
cd backend-services
python combined_service.py

# Or start individual services
cd backend-services/api-gateway
uvicorn app.main:app --reload --port 8000
```

### 2. Access Swagger UI

Once your services are running, access the Swagger UI documentation:

- API Gateway: http://localhost:8000/docs
- Auth Service: http://localhost:8001/docs
- Conversation Service: http://localhost:8002/docs
- Voice Service: http://localhost:8003/docs

### 3. Using Swagger UI for Testing

1. **View all endpoints**: Organized by tags and HTTP methods
2. **See request parameters**: Required and optional parameters for each endpoint
3. **Execute requests**: Send requests directly from the browser
4. **View responses**: See the actual response from your API

#### Testing Authentication

For endpoints that require authentication:

1. First, use the `/api/v1/auth/login` endpoint to get a token
2. Click the "Authorize" button at the top of the Swagger UI
3. Enter your token in the format: `Bearer your_token_here`
4. Click "Authorize"
5. Now you can test authenticated endpoints

## Using the Test Script

A Python script is provided for testing the API endpoints.

### 1. Install Dependencies

```bash
cd backend-services
pip install requests python-dotenv
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend-services` directory with your test credentials:

```
TEST_EMAIL=your_email@example.com
TEST_PASSWORD=your_password
```

### 3. Run the Test Script

```bash
cd backend-services
python test_api.py
```

The script will:

1. Login to get an authentication token
2. Get all conversations
3. Create a new conversation
4. Get the created conversation
5. Create a message in the conversation
6. Get all messages in the conversation
7. Create a voice session
8. Get the voice session status
9. Get the user profile

## Manual Testing with curl

You can also test the API endpoints using curl commands.

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email@example.com", "password": "your_password"}'
```

### Conversations

```bash
# Get all conversations
curl -X GET http://localhost:8000/api/v1/conversations \
  -H "Authorization: Bearer your_token_here"

# Create a conversation
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{"title": "Test Conversation", "metadata": {}, "tags": ["test"]}'

# Get a specific conversation
curl -X GET http://localhost:8000/api/v1/conversations/your_conversation_id \
  -H "Authorization: Bearer your_token_here"
```

### Messages

```bash
# Create a message
curl -X POST http://localhost:8000/api/v1/conversations/your_conversation_id/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{"role": "user", "content": "Hello, this is a test message", "message_type": "text"}'

# Get all messages in a conversation
curl -X GET http://localhost:8000/api/v1/conversations/your_conversation_id/messages \
  -H "Authorization: Bearer your_token_here"
```

### Voice

```bash
# Create a voice session
curl -X POST http://localhost:8000/api/v1/voice/session/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{"conversation_id": "your_conversation_id", "metadata": {"instructions": "You are a helpful medical assistant."}}'

# Get voice session status
curl -X GET http://localhost:8000/api/v1/voice/session/your_session_id/status \
  -H "Authorization: Bearer your_token_here"
```

### User Profile

```bash
# Get user profile
curl -X GET http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer your_token_here"
```

## Troubleshooting

### Common Issues

1. **Authentication errors**: Make sure you're using a valid token and including it in the Authorization header
2. **404 errors**: Check that your endpoint paths are correct
3. **500 errors**: Look at the server logs for detailed error information
4. **CORS errors**: If testing from a frontend, ensure CORS is properly configured

### Checking Service Status

To check if all services are running:

```bash
# List all running processes
ps aux | grep uvicorn
```

You should see processes for each service (api-gateway, auth-service, conversation-service, voice-service).
