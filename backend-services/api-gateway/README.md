# Medical Chatbot API Gateway

This is the API Gateway service for the Medical Chatbot application. It provides a unified interface for all backend services following a microservice architecture.

## Features

- Authentication and user management (via Auth Service)
- Conversation management (via Conversation Service)
- Voice session management (via Voice Service)
- User profile management (via Auth Service)
- Integration with Voice Service for real-time voice communication using OpenAI Realtime API

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Supabase account (for authentication)
- Microservices running (example configuration - ports can be adjusted in your .env file):
  - Auth Service (default: port 8001)
  - Conversation Service (default: port 8002)
  - Voice Service (default: port 8003)

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
# Example .env file - Replace with your actual values

# Supabase credentials
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# OpenAI API key (used by conversation service)
OPENAI_API_KEY=your_openai_api_key

# Microservices URLs (example values - adjust as needed)
AUTH_SERVICE_URL=http://localhost:8001  # Example - Auth service address
CONVERSATION_SERVICE_URL=http://localhost:8002  # Example - Conversation service address
VOICE_SERVICE_URL=http://localhost:8003  # Example - Voice service address

# RabbitMQ configuration (if needed)
# RABBITMQ_HOST=localhost  # Example - RabbitMQ host
# RABBITMQ_PORT=5672  # Example - RabbitMQ port
# RABBITMQ_USER=guest  # Example - RabbitMQ username
# RABBITMQ_PASSWORD=guest  # Example - RabbitMQ password
```

## Docker

To build and run the Docker container:

```
docker build -t medical-chatbot-api-gateway .
docker run -p 8000:8000 --env-file .env medical-chatbot-api-gateway
```
