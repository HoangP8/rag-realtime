# Voice Service for Medical Chatbot

This service provides real-time speech-to-speech capabilities for the Medical Chatbot using LiveKit WebRTC integration and an event-driven architecture with RabbitMQ.

## Features

- Real-time voice communication using LiveKit WebRTC
- WebSocket API for direct client communication
- Event-driven architecture with RabbitMQ
- Support for multiple concurrent voice sessions
- Session management and monitoring

## Prerequisites

- Python 3.8+
- Docker (for running RabbitMQ)
- LiveKit server (for WebRTC communication)
- Supabase account (for authentication and database)
- OpenAI API key (for speech-to-text and text-to-speech)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd backend-services
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file and add your API keys and configuration.

3. Install dependencies:
   ```bash
   cd voice-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the Service

### Using the Run Script

The easiest way to run the voice service is to use the provided script:

```bash
cd backend-services
chmod +x run_voice_service.sh
./run_voice_service.sh
```

This script will:
1. Start RabbitMQ in a Docker container if it's not already running
2. Create a Python virtual environment if it doesn't exist
3. Install dependencies
4. Start the voice service on port 8003

### Manual Setup

If you prefer to set up the service manually:

1. Start RabbitMQ:
   ```bash
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
   ```

2. Start the voice service:
   ```bash
   cd voice-service
   uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
   ```

## Testing the Voice Mode

The service includes several test scripts to help you test the voice mode without a frontend application.

### 1. Testing Session Management

Use the `test_voice_session.sh` script to create, check, and delete voice sessions:

```bash
cd voice-service
chmod +x scripts/test_voice_session.sh
./scripts/test_voice_session.sh
```

Before running, edit the script to set your API URL and authentication token.

### 2. Testing WebSocket Communication

Use the `test_voice_websocket.py` script to test real-time communication via WebSocket:

```bash
cd voice-service
python scripts/test_voice_websocket.py <session-id> --url ws://localhost:8000
```

Replace `<session-id>` with the session ID obtained from the session creation API.

This script will:
1. Connect to the WebSocket endpoint
2. Start a conversation
3. Send a test message
4. Enter interactive mode where you can type messages and receive responses
5. Stop the conversation when you type 'exit'

### 3. Testing LiveKit Connection

Use the `test_livekit_connection.py` script to test the LiveKit WebRTC connection:

```bash
cd voice-service
python scripts/test_livekit_connection.py <token> --url wss://your-livekit-server
```

Replace `<token>` with the token obtained from the session creation API and update the LiveKit server URL.

### 4. Testing OpenAI Realtime API Integration

Use the `test_openai_realtime.py` script to test the OpenAI Realtime API integration:

```bash
cd voice-service
python scripts/test_openai_realtime.py --url http://localhost:8003
```

This script will:
1. Create a new voice session
2. Connect to the WebSocket endpoint
3. Start a conversation
4. Send a test message
5. Enter interactive mode where you can type messages and receive responses
6. Stop the conversation when you type 'exit'
7. Delete the session

Options:
- `--url`: API URL (default: http://localhost:8003)
- `--token`: Authentication token (if required)
- `--session-id`: Use an existing session ID instead of creating a new one
- `--keep`: Keep the session after the test (don't delete it)

## API Endpoints

### Session Management

- **Create Session**: `POST /api/v1/session/create`
  ```json
  {
    "conversation_id": "optional-uuid",
    "metadata": {
      "instructions": "You are a medical assistant. Help the user with their medical questions."
    }
  }
  ```

- **Get Session Status**: `GET /api/v1/session/{session_id}/status`
  ```json
  {
    "voice_settings": {
      "voice_id": "alloy",
      "stability": 0.5,
      "similarity_boost": 0.5,
      "temperature": 0.8,
      "max_output_tokens": 2048
    },
    "transcription_settings": {
      "language": "en",
      "model": "whisper-1"
    }
  }
  ```

- **Delete Session**: `DELETE /api/v1/session/{session_id}`

### Real-time Communication

- **WebSocket**: `ws://localhost:8003/api/v1/ws/{session_id}`

  Messages to send:
  ```json
  {"type": "control", "action": "start"}
  {"type": "text", "text": "Hello, how are you?"}
  {"type": "audio", "data": "base64_audio_data"}
  {"type": "control", "action": "stop"}
  ```

### Webhooks

- **LiveKit Webhook**: `POST /api/v1/webhooks/livekit`

## Architecture

The voice service uses an event-driven architecture with the following components:

1. **Session Manager**: Handles multiple concurrent voice sessions
2. **Voice Agent**: Manages real-time communication for a single session using OpenAI Realtime API
3. **RabbitMQ**: Message broker for event-driven communication
4. **LiveKit**: WebRTC service for real-time audio streaming
5. **OpenAI**: For speech-to-text and text-to-speech processing using the Realtime API

### Directory Structure

```
voice-service/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── v1/              # API version 1
│   │   │   ├── realtime.py  # Voice API and WebSocket endpoints
│   │   │   └── webhooks.py  # Webhook handlers
│   │   └── router.py        # API router
│   ├── livekit/             # LiveKit integration
│   │   ├── config.py        # LiveKit configuration
│   │   ├── connection.py    # LiveKit connection management
│   │   └── session.py       # LiveKit session management
│   ├── messaging/           # Messaging components
│   │   └── rabbitmq.py      # RabbitMQ integration
│   ├── realtime/            # Real-time components
│   │   ├── session_manager.py # Session management
│   │   └── voice_agent.py   # Voice agent for real-time communication
│   ├── services/            # Service layer
│   │   └── llm.py           # LLM service
│   ├── config.py            # Application configuration
│   ├── dependencies.py      # Dependency injection
│   ├── main.py              # Application entry point
│   └── models.py            # Data models
├── logs/                    # Log files
├── scripts/                 # Test scripts
│   ├── test_livekit_connection.py  # Test LiveKit connection
│   ├── test_openai_realtime.py    # Test OpenAI Realtime API
│   └── test_voice_websocket.py     # Test WebSocket communication
└── requirements.txt         # Dependencies
```

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

### Logs

Check the logs for more detailed error information:

```bash
cd voice-service
tail -f logs/voice-service.log
```

## License

[Your License]
