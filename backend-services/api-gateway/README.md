# Medical Chatbot API Gateway

This is the API Gateway service for the Medical Chatbot application. It provides a unified interface for all backend services.

## Features

- Authentication and user management
- Conversation management
- Voice session management
- User profile management
- Integration with OpenAI for LLM capabilities
- Integration with LiveKit for real-time voice communication

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Supabase account
- OpenAI API key
- LiveKit account

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables (see `.env.example`)
4. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_url
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Docker

To build and run the Docker container:

```
docker build -t medical-chatbot-api-gateway .
docker run -p 8000:8000 --env-file .env medical-chatbot-api-gateway
```
