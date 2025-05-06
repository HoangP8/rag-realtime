# Voice Service

A simplified, modern voice service for the Medical Chatbot using LiveKit Agents.

## Directory Structure

```
voice-service-new/
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

1. Install dependencies:
   ```bash
   pip install "livekit-agents[openai]~=1.0" fastapi uvicorn supabase pydantic-settings
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API keys
   ```

3. Run the service:
   ```bash
   ./scripts/run.sh
   ```

4. Test the service:
   ```bash
   ./scripts/test.sh
   ```

## API Endpoints

- `POST /api/v1/voice/session`: Create a new voice session
- `GET /api/v1/voice/session/{session_id}`: Get a voice session
- `DELETE /api/v1/voice/session/{session_id}`: Delete a voice session
- `WebSocket /api/v1/voice/ws/{session_id}`: WebSocket for session status updates

## Architecture

This service follows a clean architecture approach with:

1. **Clear Separation of Concerns**:
   - API endpoints in `app/api/routes.py`
   - Business logic in `app/services/`
   - Utility functions in `app/utils/`
   - Agent-specific code in `agent/`

2. **Simplified Session Management**:
   - Simple session service focused on LiveKit room management
   - Storage service for database operations

3. **LiveKit Agents Integration**:
   - Uses the LiveKit Agents worker API
   - Handles multiple concurrent sessions
   - Automatic room creation and management

## Environment Variables

- `LIVEKIT_URL`: LiveKit server URL
- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `OPENAI_API_KEY`: OpenAI API key
- `SUPABASE_URL`: Supabase URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
