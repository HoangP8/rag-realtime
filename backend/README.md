# Medical Chatbot Backend Services

This repository contains the backend services for the Medical Chatbot application, which allows users to speak with an AI assistant about medical topics in a natural, conversational way.

## Architecture

The backend is built using a microservices architecture with the following components:

1. **API Gateway**: Central entry point for all client requests (Port 8000)
2. **Auth Service**: Handles user authentication and authorization (Port 8001)
3. **Conversation Service**: Manages conversations, messages, and LLM interactions (Port 8002)
4. **Voice Service**: Handles real-time voice communication via LiveKit and OpenAI Realtime API (Port 8003)
   - Voice API: Manages voice sessions and client connections
   - LiveKit Agent Worker: Handles real-time speech-to-speech functionality

## App Structure

```
backend/
├── api-gateway/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── conversations.py
│   │   │   │   ├── profile.py
│   │   │   │   └── voice.py
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   └── __init__.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── supabase.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   ├── profile.py
│   │   │   └── voice.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   ├── profile.py
│   │   │   └── voice.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── auth-service/
│   ├── app/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── router.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── conversation-service/
│   ├── app/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── llm.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── router.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── voice-service/
│   ├── agent/
│   │   ├── scripts/
│   │   │   └── download_vectorstore.sh
│   │   ├── text_benchmark.py
│   │   ├── vectorstore.py
│   │   ├── voice_benchmark.py
│   │   ├── voce_benchmark.txt
│   │   └── worker.py
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   └── storage.py
│   │   ├── utils/
│   │   │   └── livekit.py
│   │   ├── config.py
│   │   ├── models.py
│   │   └── main.py
│   ├── scripts/
│   │   ├── run_api.sh
│   │   └── run_agent.sh
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   ├── fly.worker.toml
│   └── requirements.txt
│
├── database/
│   └── schema.sql
│
├── .dockerignore
├── .gitignore
├── API_DOCUMENTATION.md
├── API_TESTING.md
├── DEPLOYMENT.md
├── Dockerfile
├── fly.toml
├── README.md
├── combined_service.py
├── copy_env.py
├── docker-compose.yml
└── test_api.py
```

## Technologies

- **FastAPI**: Modern, high-performance web framework for building APIs
- **Supabase**: PostgreSQL database, authentication, and storage
- **LiveKit**: Real-time voice communication with WebRTC
- **OpenAI**: GPT models for natural language processing and voice synthesis

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- Supabase account
- OpenAI API key
- LiveKit account
- flyctl (for deployment to fly.io)

### Environment Setup

Create a `.env.local` file in the root directory with the following variables:

> **Note**: You can create a single `.env.local` file in the `backend` directory and run the `copy_env.py` script to copy it to all service directories:
> ```bash
> cd backend
> python copy_env.py
> ```

```
# Supabase credentials (required)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# OpenAI API key (required)
OPENAI_API_KEY=your_openai_api_key

# LiveKit settings (for voice service)
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_url

# Deepgram API key (optional, for alternative transcription)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Service URLs (for local development)
AUTH_SERVICE_URL=http://localhost:8001
CONVERSATION_SERVICE_URL=http://localhost:8002
VOICE_SERVICE_URL=http://localhost:8003

# RabbitMQ configuration (if needed)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
```

### Running Locally

1. Install dependencies for each service:
   ```bash
   cd api-gateway && pip install -r requirements.txt
   cd ../auth-service && pip install -r requirements.txt
   cd ../conversation-service && pip install -r requirements.txt
   cd ../voice-service && pip install -r requirements.txt
   ```

2. Run each service in a separate terminal:
   ```bash
   cd api-gateway && uvicorn app.main:app --reload --port 8000
   cd auth-service && uvicorn app.main:app --reload --port 8001
   cd conversation-service && uvicorn app.main:app --reload --port 8002
   cd voice-service && uvicorn app.main:app --reload --port 8003
   ```

3. For the voice service, also run the LiveKit agent worker:
   ```bash
   cd voice-service && bash scripts/run_agent.sh
   ```

### Running with Docker

For local testing with Docker:

```bash
# Build and run the main backend services
cd backend
docker build -t medical-chatbot .
docker run -p 8000:8000 --env-file .env.local medical-chatbot

# Build and run the voice service worker
cd voice-service
docker build -t worker-agent -f Dockerfile.worker .
docker run --env-file .env.local worker-agent
```

## API Documentation

Once the services are running, you can access the API documentation at:

- API Gateway: `http://localhost:8000/docs`
- Auth Service: `http://localhost:8001/docs`
- Conversation Service: `http://localhost:8002/docs`
- Voice Service: `http://localhost:8003/docs`

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

The Voice Service handles real-time voice communication using LiveKit WebRTC integration. It consists of two main components:

1. **Voice API**: FastAPI service that manages voice sessions and provides WebSocket connections
2. **LiveKit Agent Worker**: Handles real-time speech-to-speech functionality using OpenAI's Realtime API

#### Voice Service Features

- Real-time speech-to-speech communication
- Automatic transcription of conversations
- Storage of conversation history
- Multiple concurrent voice sessions
- WebSocket status updates

#### Voice Mode API Endpoints

- **Create Session**: `POST /api/v1/voice/session`
  ```json
  {
    "conversation_id": "optional-uuid",
    "instructions": "You are a medical assistant. Help the user with their medical questions.",
    "voice_settings": {
      "voice_id": "alloy",
      "temperature": 0.8,
      "max_output_tokens": 2048
    },
    "metadata": {}
  }
  ```

- **Get Session**: `GET /api/v1/voice/session/{session_id}`

- **Get Session Status**: `GET /api/v1/voice/session/{session_id}/status`

- **Update Session Config**: `PUT /api/v1/voice/session/{session_id}/config`

- **Delete Session**: `DELETE /api/v1/voice/session/{session_id}`

  Messages to send:
  ```json
  {"type":"control","action":"start"}
  {"type":"text","text":"Hello, how are you?"}
  {"type":"audio","data":"base64_audio_data"}
  {"type":"control","action":"stop"}
  ```

## Testing

### Testing with cURL

```bash
# Create a voice session
curl -X POST http://localhost:8000/api/v1/voice/session \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instructions": "You are a medical assistant. Help the user with their medical questions."}'

# Get session status
curl -X GET http://localhost:8000/api/v1/voice/session/SESSION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"

# Delete session
curl -X DELETE http://localhost:8000/api/v1/voice/session/SESSION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Common Issues

1. **LiveKit Connection Error**:
   - Verify LiveKit server is running
   - Check LiveKit API key and secret in `.env.local` file
   - Ensure the token is valid and not expired

3. **Voice Service Issues**:
   - Ensure both the API and worker components are running
   - Check LiveKit credentials are correctly set
   - Verify OpenAI API key has access to Realtime API

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deployment to fly.io

The application is deployed as two separate fly.io apps:

1. **Main Backend Services** (`medbot-backend`): API Gateway, Auth, Conversation, and Voice API
2. **Voice Agent Worker** (`medbot-agent`): LiveKit agent for real-time voice processing

```bash
# Navigate to the backend directory
cd backend

# Deploy main backend services
flyctl launch --config fly.toml
# Set the secrets
cat .env.local | tr '\n' ' ' | xargs flyctl secrets set
# For subsequent deployments
flyctl deploy --config fly.toml

# Deploy voice agent worker
cd voice-service
flyctl launch --config fly.worker.toml
# Set the secrets
cat .env.local | tr '\n' ' ' | xargs flyctl -a medbot-agent secrets set
# For subsequent deployments
flyctl deploy --config fly.worker.toml
```
