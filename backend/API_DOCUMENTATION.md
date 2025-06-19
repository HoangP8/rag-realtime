# Medical Chatbot API Documentation

This document provides comprehensive documentation for the Medical Chatbot API, designed to help frontend developers integrate with the backend services.

## Table of Contents

1. [Overview](#overview)
2. [Base URLs](#base-urls)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication-endpoints)
   - [Conversations](#conversation-endpoints)
   - [Messages](#message-endpoints)
   - [Voice](#voice-endpoints)
   - [User Profile](#user-profile-endpoints)
5. [WebSocket API](#websocket-api)
6. [Error Handling](#error-handling)
7. [Data Models](#data-models)
8. [Examples](#examples)

## Overview

The Medical Chatbot API follows RESTful principles and uses JSON for request and response bodies. The API is organized into several microservices, but frontend developers only need to interact with the API Gateway, which routes requests to the appropriate services.

## Base URLs

**Development**: `http://localhost:8000`

**Production**: `https://medbot-backend.fly.dev`

All API endpoints are prefixed with `/api/v1`.

## Authentication

The API uses JWT (JSON Web Token) for authentication. To access protected endpoints, include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Obtaining a Token

To obtain a token, use the login endpoint. The token will be valid for a limited time and can be refreshed using the refresh endpoint.

## API Endpoints

### Authentication Endpoints

#### Register a New User

- **URL**: `/api/v1/auth/register`
- **Method**: `POST`
- **Auth Required**: No
- **Description**: Register a new user account

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response** (201 Created):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2023-01-01T12:00:00Z"
}
```

#### Login

- **URL**: `/api/v1/auth/login`
- **Method**: `POST`
- **Auth Required**: No
- **Description**: Authenticate a user and get a JWT token

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2023-01-01T13:00:00Z",
  "expires_in": 3600
}
```

#### Refresh Token

- **URL**: `/api/v1/auth/refresh`
- **Method**: `POST`
- **Auth Required**: No
- **Description**: Get a new access token using a refresh token

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2023-01-01T14:00:00Z",
  "expires_in": 3600
}
```

#### Logout

- **URL**: `/api/v1/auth/logout`
- **Method**: `POST`
- **Auth Required**: Yes
- **Description**: Invalidate the current token

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

#### Validate Token

- **URL**: `/api/v1/auth/validate`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Validate the current token and get user info

**Response** (200 OK):
```json
{
  "valid": true,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Conversation Endpoints

#### Get All Conversations

- **URL**: `/api/v1/conversations`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get all conversations for the current user

**Query Parameters**:
- `limit` (optional): Maximum number of conversations to return (default: 50)
- `offset` (optional): Number of conversations to skip (default: 0)
- `archived` (optional): Include archived conversations (default: false)

**Response** (200 OK):
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174001",
    "title": "Conversation Title",
    "metadata": {
      "key": "value"
    },
    "tags": ["headache", "consultation"],
    "is_archived": false,
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:30:00Z"
  }
]
```

#### Create a New Conversation

- **URL**: `/api/v1/conversations`
- **Method**: `POST`
- **Auth Required**: Yes
- **Description**: Create a new conversation

**Request Body**:
```json
{
  "title": "New Medical Consultation",
  "metadata": {
    "key": "value"
  },
  "tags": ["consultation"]
}
```

**Response** (201 Created):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "title": "New Medical Consultation",
  "metadata": {
    "key": "value"
  },
  "tags": ["consultation"],
  "is_archived": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

#### Get a Specific Conversation

- **URL**: `/api/v1/conversations/{conversation_id}`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get details of a specific conversation

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "title": "Medical Consultation",
  "metadata": {
    "key": "value"
  },
  "tags": ["headache", "consultation"],
  "is_archived": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:30:00Z"
}
```

#### Update a Conversation

- **URL**: `/api/v1/conversations/{conversation_id}`
- **Method**: `PUT`
- **Auth Required**: Yes
- **Description**: Update a conversation

**Request Body**:
```json
{
  "title": "Updated Medical Consultation",
  "metadata": {
    "updated_by": "user"
  },
  "tags": ["headache", "consultation", "follow-up"],
  "is_archived": false
}
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "title": "Updated Medical Consultation",
  "metadata": {
    "updated_by": "user"
  },
  "tags": ["headache", "consultation", "follow-up"],
  "is_archived": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T13:00:00Z"
}
```

#### Delete a Conversation

- **URL**: `/api/v1/conversations/{conversation_id}`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Description**: Delete a conversation and all its messages

**Response** (204 No Content)

### Message Endpoints

#### Get Messages for a Conversation

- **URL**: `/api/v1/conversations/{conversation_id}/messages`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get all messages for a specific conversation

**Query Parameters**:
- `limit` (optional): Maximum number of messages to return (default: 50)
- `offset` (optional): Number of messages to skip (default: 0)
- `order` (optional): Sort order - "asc" or "desc" (default: "asc")

**Response** (200 OK):
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "I've been experiencing headaches and fatigue for the past week.",
    "message_type": "text",
    "voice_url": null,
    "metadata": {},
    "created_at": "2023-01-01T12:00:00Z"
  },
  {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "I understand you've been experiencing headaches and fatigue. Can you tell me more about the severity and frequency of these symptoms?",
    "message_type": "text",
    "voice_url": null,
    "metadata": {},
    "created_at": "2023-01-01T12:01:00Z"
  }
]
```

#### Send a Message

- **URL**: `/api/v1/conversations/{conversation_id}/messages`
- **Method**: `POST`
- **Auth Required**: Yes
- **Description**: Send a new message to a conversation. When a user message is created, the system will automatically generate an assistant response.

**Request Body**:
```json
{
  "role": "user",
  "content": "I've been experiencing headaches and fatigue for the past week.",
  "message_type": "text",
  "metadata": {
    "source": "web"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174002",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "content": "I've been experiencing headaches and fatigue for the past week.",
  "message_type": "text",
  "voice_url": null,
  "metadata": {}
}
```

#### Get a Specific Message

- **URL**: `/api/v1/messages/{message_id}`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get details of a specific message

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174002",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "content": "I've been experiencing headaches and fatigue for the past week.",
  "message_type": "text",
  "voice_url": null,
  "metadata": {},
  "created_at": "2023-01-01T12:05:00Z"
}
```

### Voice Endpoints

#### Create a Voice Session

- **URL**: `/api/v1/voice/session`
- **Method**: `POST`
- **Auth Required**: Yes
- **Description**: Create a new voice session for real-time voice communication

**Request Body**:
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "metadata": {
    "voice_settings": {
      "voice_id": "alloy",
      "temperature": 0.8,
      "max_output_tokens": 2048
    },
  }
}
```

**Response** (201 Created):
```json
{
  "id": "session_123456",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "token": "session_token_abc123",
  "metadata": {
    "session_type": "consultation"
  },
  "config": {
    "voice_settings": {
      "voice_id": "alloy",
      "temperature": 0.8,
      "max_output_tokens": 2048
    },
    "transcription_settings": {
      "language": "en",
      "model": "whisper-1"
    }
  },
  "created_at": "2023-01-01T12:10:00Z"
}
```

#### Get a Voice Session

- **URL**: `/api/v1/voice/session/{session_id}`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get details of a specific voice session

**Response** (200 OK):
```json
{
  "id": "session_123456",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "token": "session_token_abc123",
  "metadata": {
    "instructions": "You are a helpful medical assistant."
  },
  "config": {
    "voice_settings": {
      "voice_id": "alloy",
      "temperature": 0.8,
      "max_output_tokens": 2048
    },
    "transcription_settings": {
      "language": "en",
      "model": "whisper-1"
    }
  },
  "created_at": "2023-01-01T12:00:00Z"
}
```

#### Delete a Voice Session

- **URL**: `/api/v1/voice/session/{session_id}`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Description**: Delete a voice session and end the real-time connection

**Response** (204 No Content)

### User Profile Endpoints

#### Get User Profile

- **URL**: `/api/v1/profile`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get the current user's profile

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "medical_history_id": null,
  "preferences": {
    "voice_preference": "alloy",
    "theme": "light",
    "notifications_enabled": true,
    "isVietnamese": true,
    "useRAG": true,
  },
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

#### Update User Profile

- **URL**: `/api/v1/profile`
- **Method**: `PUT`
- **Auth Required**: Yes
- **Description**: Update the current user's profile

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "date_of_birth": "1990-01-01",
  "preferences": {
    "language": "en",
    "voice_preference": "nova",
    "theme": "dark"
  }
}
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Smith",
  "date_of_birth": "1990-01-01",
  "medical_history_id": null,
  "preferences": {
    "language": "en",
    "voice_preference": "nova",
    "theme": "dark"
  },
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T14:00:00Z"
}
```

#### Get User Preferences

- **URL**: `/api/v1/profile/preferences`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get the current user's preferences

**Response** (200 OK):
```json
{
  "language": "en",
  "voice_preference": "alloy",
  "theme": "light",
  "notifications_enabled": true
}
```

#### Update User Preferences

- **URL**: `/api/v1/profile/preferences`
- **Method**: `PUT`
- **Auth Required**: Yes
- **Description**: Update the current user's preferences

**Request Body**:
```json
{
  "voice_preference": "nova",
  "theme": "dark",
  "notifications_enabled": false
}
```

**Response** (200 OK):
```json
{
  "language": "en",
  "voice_preference": "nova",
  "theme": "dark",
  "notifications_enabled": false
}
```

## WebSocket API

### Voice Communication WebSocket

- **URL**: `ws://localhost:8000/api/v1/voice/ws/{session_id}` (Development)
- **URL**: `wss://medbot-backend.fly.dev/api/v1/voice/ws/{session_id}` (Production)
- **Auth Required**: Valid session must be created first
- **Description**: Real-time voice communication with the AI assistant using LiveKit WebRTC

#### Connection

Connect to the WebSocket using the session ID obtained from creating a voice session:

```javascript
const sessionId = "session_123456";
const wsUrl = `ws://localhost:8000/api/v1/voice/ws/${sessionId}`;
const socket = new WebSocket(wsUrl);
```

#### Client to Server Messages

**Control Messages**:
```json
{
  "type": "control",
  "action": "start"
}
```

Available actions: `start`, `stop`, `pause`, `resume`

**Text Messages**:
```json
{
  "type": "text",
  "text": "Hello, I have a medical question."
}
```

**Audio Messages**:
```json
{
  "type": "audio",
  "data": "base64_encoded_audio_data"
}
```

**Configuration Updates**:
```json
{
  "type": "config",
  "config": {
    "voice_settings": {
      "voice_id": "nova",
      "temperature": 0.7
    }
  }
}
```

#### Server to Client Messages

**Connection Status**:
```json
{
  "type": "status",
  "status": "connected",
  "message": "Connected to voice session",
  "session_id": "session_123456"
}
```

**Transcription (User Speech)**:
```json
{
  "type": "transcription",
  "text": "Hello, I have a medical question.",
  "is_final": true,
  "confidence": 0.95,
  "user_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**AI Response (Audio)**:
```json
{
  "type": "audio",
  "data": "base64_encoded_audio_data",
  "format": "opus",
  "duration": 2.5
}
```

**AI Response (Text)**:
```json
{
  "type": "response",
  "text": "I understand you have a medical question. Please tell me more about your symptoms.",
  "message_id": "123e4567-e89b-12d3-a456-426614174004"
}
```

**Session Events**:
```json
{
  "type": "session_event",
  "event": "participant_connected",
  "data": {
    "participant_id": "user_123",
    "timestamp": "2023-01-01T12:15:00Z"
  }
}
```

**Error Messages**:
```json
{
  "type": "error",
  "code": "SESSION_EXPIRED",
  "message": "Voice session has expired. Please create a new session.",
  "details": {
    "session_id": "session_123456",
    "timestamp": "2023-01-01T12:20:00Z"
  }
}
```

## Error Handling

The API uses standard HTTP status codes and returns error responses in the following format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {},
    "timestamp": "2023-01-01T12:00:00Z"
  }
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content to return
- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Authentication Error Codes

- `INVALID_TOKEN`: JWT token is invalid or expired
- `TOKEN_REQUIRED`: Authorization header missing
- `REFRESH_TOKEN_INVALID`: Refresh token is invalid or expired
- `ACCESS_DENIED`: User doesn't have permission to access resource

### Voice Session Error Codes

- `SESSION_NOT_FOUND`: Voice session does not exist
- `SESSION_EXPIRED`: Voice session has expired
- `SESSION_INACTIVE`: Voice session is not active
- `LIVEKIT_CONNECTION_ERROR`: Unable to connect to LiveKit server
- `AUDIO_PROCESSING_ERROR`: Error processing audio data
- `TRANSCRIPTION_ERROR`: Error transcribing audio
- `VOICE_SYNTHESIS_ERROR`: Error generating voice response

### Validation Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": {
        "email": ["Invalid email format"],
        "password": ["Password must be at least 8 characters"]
      }
    }
  }
}
```

## Data Models

### User

```json
{
  "id": "UUID",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "date",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Token Response

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "string",
  "expires_at": "datetime",
  "expires_in": "integer"
}
```

### Conversation

```json
{
  "id": "UUID",
  "user_id": "UUID",
  "title": "string",
  "metadata": "object",
  "tags": ["string"],
  "is_archived": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Message

```json
{
  "id": "UUID",
  "conversation_id": "UUID",
  "role": "string", // "user", "assistant", or "system"
  "content": "string",
  "message_type": "string", // "text" or "voice"
  "voice_url": "string or null",
  "metadata": "object",
  "created_at": "datetime"
}
```

### Voice Session

```json
{
  "id": "string",
  "user_id": "UUID",
  "conversation_id": "UUID",
  "status": "string", // "active", "inactive", "error", or "expired"
  "token": "string",
  "metadata": "object",
  "config": {
    "voice_settings": {
      "voice_id": "string", // "alloy", "echo", "fable", "onyx", "nova", "shimmer"
      "temperature": "float", // 0.0 - 1.0
      "max_output_tokens": "integer"
    },
    "transcription_settings": {
      "language": "string", // "en", "es", "fr", etc.
      "model": "string" // "whisper-1"
    }
  },
  "created_at": "datetime"
}
```

### User Profile

```json
{
  "id": "UUID",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "date",
  "medical_history_id": "UUID or null",
  "preferences": {
    "language": "string",
    "voice_preference": "string",
    "theme": "string",
    "notifications_enabled": "boolean"
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Examples

### Example: Complete Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "securepassword123"
  }'

# 3. Use the access token for authenticated requests
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 4. Validate token
curl -X GET http://localhost:8000/api/v1/auth/validate \
  -H "Authorization: Bearer $TOKEN"
```

### Example: Text Conversation Flow

```bash
# 1. Create a conversation
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Headache Consultation",
    "tags": ["headache", "consultation"]
  }'

# Response: {"id": "conv_123", ...}

# 2. Send a message
curl -X POST http://localhost:8000/api/v1/conversations/conv_123/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "role": "user",
    "content": "I have been experiencing severe headaches for the past 3 days.",
    "message_type": "text"
  }'

# 3. Get conversation messages
curl -X GET http://localhost:8000/api/v1/conversations/conv_123/messages \
  -H "Authorization: Bearer $TOKEN"
```

### Example: Voice Session Flow

```bash
# 1. Create a voice session
curl -X POST http://localhost:8000/api/v1/voice/session \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "conversation_id": "conv_123",
    "instructions": "You are a medical assistant. Help the user with their symptoms.",
    "voice_settings": {
      "voice_id": "alloy",
      "temperature": 0.8,
      "max_output_tokens": 2048
    }
  }'

# Response: {"id": "session_456", ...}

```


```bash
# 2. Delete the voice session when done
curl -X DELETE http://localhost:8000/api/v1/voice/session/session_456 \
  -H "Authorization: Bearer $TOKEN"
```

### Example: User Profile Management

```bash
# 1. Get user profile
curl -X GET http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer $TOKEN"

# 2. Update user profile
curl -X PUT http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "preferences": {
      "voice_preference": "nova",
      "theme": "dark"
    }'

# 3. Update only preferences
curl -X PUT http://localhost:8000/api/v1/profile/preferences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "notifications_enabled": false,
    "voice_preference": "shimmer"
  }'
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authentication endpoints**: 10 requests per minute
- **Conversation endpoints**: 100 requests per minute
- **Message endpoints**: 50 requests per minute
- **Voice session creation**: 5 sessions per minute
- **Profile endpoints**: 20 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640995200
```

## Support

For API support and questions:

- **Documentation**: This document
- **Email**: medbot.capstone@gmail.com
- **GitHub Issues**: https://github.com/HoangP8/rag-realtime/issues

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial API release
- Authentication endpoints
- Conversation and message management
- Voice session support with LiveKit integration
- User profile management
- Real-time WebSocket communication
