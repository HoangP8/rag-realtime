# Voice Service

A simplified, modern voice service for the Medical Chatbot using LiveKit Agents.

## Overview

This service provides real-time voice communication capabilities for the Medical Chatbot application. It uses LiveKit's WebRTC infrastructure and Agents framework to create voice sessions between users and AI assistants.

## Features

- Real-time speech-to-speech communication
- Automatic transcription of conversations
- Storage of conversation history
- Multiple concurrent voice sessions
- WebSocket status updates

## Architecture

The service follows a clean architecture approach with:

1. **API Layer**: FastAPI endpoints for creating, retrieving, and deleting voice sessions
2. **Service Layer**: Business logic for session management and storage operations
3. **Agent Layer**: LiveKit Agents implementation for real-time voice processing
4. **Utility Layer**: Helper functions for LiveKit integration

## Directory Structure

```
voice-service/
├── app/                      # Main application code
│   ├── api/                  # API endpoints
│   ├── services/             # Business logic
│   ├── utils/                # Utility functions
│   ├── config.py             # Configuration settings
│   ├── main.py               # FastAPI application
│   └── models.py             # Pydantic models
├── agent/                    # Agent-specific code
│   ├── agent.py              # Agent implementation
│   └── worker.py             # LiveKit agent worker
└── scripts/                  # Scripts for running and testing
    ├── run.sh                # Script to run both service and agent
    └── test.sh               # Test script
```

## Getting Started

### Prerequisites

- Python 3.9+
- LiveKit server
- Supabase account
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/medical-chatbot.git
   cd medical-chatbot/backend-services/voice-service
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API keys
   ```

### Running the Service

```bash
./scripts/run.sh
```

This will start both the FastAPI service and the LiveKit Agents worker.

### Testing the Service

```bash
./scripts/test.sh
```

This will create a test session, get its details, and then delete it.

## API Endpoints

### Create a Voice Session

```
POST /api/v1/voice/session
```

Request body:
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

### Get a Voice Session

```
GET /api/v1/voice/session/{session_id}
```

### Delete a Voice Session

```
DELETE /api/v1/voice/session/{session_id}
```

### WebSocket for Status Updates

```
WebSocket /api/v1/voice/ws/{session_id}
```

## Environment Variables

- `LIVEKIT_URL`: LiveKit server URL
- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `OPENAI_API_KEY`: OpenAI API key
- `SUPABASE_URL`: Supabase URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8003)

## License


