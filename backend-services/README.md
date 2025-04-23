# Medical Chatbot Backend Services

This repository contains the backend services for the Medical Chatbot application, which allows users to speak with an AI assistant about medical topics in a natural, conversational way.

## Architecture

The backend is built using a microservices architecture with the following components:

1. **API Gateway**: Central entry point for all client requests
2. **Auth Service**: Handles user authentication and authorization
3. **Conversation Service**: Manages conversations, messages, and LLM interactions
4. **Voice Service**: Handles real-time voice communication via LiveKit and OpenAI Realtime API

## Technologies

- **FastAPI**: Modern, high-performance web framework for building APIs
- **Supabase**: PostgreSQL database, authentication, and storage
- **LiveKit**: Real-time voice communication
- **OpenAI**: GPT models for natural language processing

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- Supabase account
- OpenAI API key
- LiveKit account

### Environment Setup

Create a `.env` file in the root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_url
DEEPGRAM_API_KEY=your_deepgram_api_key
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Running Locally

1. Install dependencies for each service:
   ```
   cd api-gateway && pip install -r requirements.txt
   cd ../auth-service && pip install -r requirements.txt
   cd ../conversation-service && pip install -r requirements.txt
   cd ../voice-service && pip install -r requirements.txt
   ```

2. Run each service in a separate terminal:
   ```
   cd api-gateway && uvicorn app.main:app --reload --port 8000
   cd auth-service && uvicorn app.main:app --reload --port 8001
   cd conversation-service && uvicorn app.main:app --reload --port 8002
   cd voice-service && uvicorn app.main:app --reload --port 8003
   ```

### Running with Docker

To run all services using Docker Compose:

```
docker-compose up --build
```

## API Documentation

Once the services are running, you can access the API documentation at:

- API Gateway: `http://localhost:8000/docs`
- Auth Service: `http://localhost:8001/docs`
- Conversation Service: `http://localhost:8002/docs`
- Voice Service: `http://localhost:8003/docs`

## Troubleshooting

### Common Issues

1. **RabbitMQ Connection Error**:
   - Make sure RabbitMQ is running: `docker ps | grep rabbitmq`
   - Check RabbitMQ logs: `docker logs rabbitmq`
   - Verify connection settings in `.env` file

2. **LiveKit Connection Error**:
   - Verify LiveKit server is running
   - Check LiveKit API key and secret in `.env` file
   - Ensure the token is valid and not expired

3. **WebSocket Connection Error**:
   - Make sure the session ID is valid
   - Check that the voice service is running
   - Verify the WebSocket URL is correct

### Testing with cURL

```bash
# Create a voice session
curl -X POST http://localhost:8000/api/v1/voice/session/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"instructions": "You are a medical assistant. Help the user with their medical questions."}}'

# Get session status
curl -X GET http://localhost:8000/api/v1/voice/session/SESSION_ID/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Delete session
curl -X DELETE http://localhost:8000/api/v1/voice/session/SESSION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Testing with WebSocket Client

You can use tools like [websocat](https://github.com/vi/websocat) or [wscat](https://github.com/websockets/wscat) to test WebSocket connections:

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket endpoint
wscat -c "ws://localhost:8000/api/v1/realtime/ws/SESSION_ID"

# Send control message to start conversation
{"type":"control","action":"start"}

# Send text message
{"type":"text","text":"Hello, how are you?"}

# Send control message to stop conversation
{"type":"control","action":"stop"}
```

## Database Schema

The application uses the following main tables in Supabase:

1. **auth.users**: Managed by Supabase Auth
2. **user_profiles**: User profile information
3. **user_roles**: User roles and permissions
4. **conversations**: Conversation metadata
5. **messages**: Individual messages in conversations
6. **voice_sessions**: Voice session information

## Services

### API Gateway

The API Gateway is the entry point for all client requests. It routes requests to the appropriate service and handles cross-cutting concerns like authentication and logging.

### Auth Service

The Auth Service handles user authentication and authorization using Supabase Auth. It provides endpoints for user registration, login, token refresh, and validation.

### Conversation Service

The Conversation Service manages conversations, messages, and LLM interactions. It provides endpoints for creating, retrieving, updating, and deleting conversations and messages. It also handles generating AI responses using the OpenAI API directly.

### Voice Service

The Voice Service handles real-time voice communication using LiveKit WebRTC integration and an event-driven architecture with RabbitMQ. It provides endpoints for creating and managing voice sessions, as well as real-time speech-to-speech capabilities.

#### Running the Voice Service

To run just the voice service for testing:

```bash
chmod +x run_voice_service.sh
./run_voice_service.sh
```

This script will:
1. Start RabbitMQ in a Docker container if it's not already running
2. Create a Python virtual environment if it doesn't exist
3. Install dependencies
4. Start the voice service on port 8003

#### Testing Voice Mode

The service includes several test scripts to help you test the voice mode without a frontend application:

##### 1. Testing Session Management

Use the `test_voice_session.sh` script to create, check, and delete voice sessions:

```bash
cd voice-service
chmod +x scripts/test_voice_session.sh
./scripts/test_voice_session.sh
```

Before running, edit the script to set your API URL and authentication token.

##### 2. Testing WebSocket Communication

Use the `test_voice_websocket.py` script to test real-time communication via WebSocket:

```bash
cd voice-service
python scripts/test_voice_websocket.py <session-id> --url ws://localhost:8000
```

Replace `<session-id>` with the session ID obtained from the session creation API.

##### 3. Testing LiveKit Connection

Use the `test_livekit_connection.py` script to test the LiveKit WebRTC connection:

```bash
cd voice-service
python scripts/test_livekit_connection.py <token> --url wss://your-livekit-server
```

Replace `<token>` with the token obtained from the session creation API and update the LiveKit server URL.

#### Voice Mode API Endpoints

- **Create Session**: `POST /api/v1/voice/session/create`
  ```json
  {
    "conversation_id": "optional-uuid",
    "metadata": {
      "instructions": "You are a medical assistant. Help the user with their medical questions."
    }
  }
  ```

- **Get Session**: `GET /api/v1/voice/session/{session_id}`

- **Get Session Status**: `GET /api/v1/voice/session/{session_id}/status`

- **Update Session Config**: `PUT /api/v1/voice/session/{session_id}/config`

- **Delete Session**: `DELETE /api/v1/voice/session/{session_id}`

- **WebSocket**: `ws://localhost:8000/api/v1/realtime/ws/{session_id}`

  Messages to send:
  ```json
  {"type":"control","action":"start"}
  {"type":"text","text":"Hello, how are you?"}
  {"type":"audio","data":"base64_audio_data"}
  {"type":"control","action":"stop"}
  ```

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deployment to fly.io

```bash
# Navigate to the backend-services directory
cd backend-services

# Set up secrets (replace with your actual values)
flyctl secrets set NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
flyctl secrets set NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
flyctl secrets set OPENAI_API_KEY=your_openai_api_key

# Deploy the application
flyctl deploy
```

This will deploy all services to a single fly.io instance for cost efficiency during the trial phase.
