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

**Production**: `https://api.medicalchatbot.com` (example - replace with actual production URL)

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

### Conversation Endpoints

#### Get All Conversations

- **URL**: `/api/v1/conversations`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get all conversations for the current user

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
    "tags": ["tag1", "tag2"],
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
  "title": "New Conversation",
  "metadata": {
    "key": "value"
  },
  "tags": ["tag1", "tag2"]
}
```

**Response** (201 Created):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "title": "New Conversation",
  "metadata": {
    "key": "value"
  },
  "tags": ["tag1", "tag2"],
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
  "title": "Conversation Title",
  "metadata": {
    "key": "value"
  },
  "tags": ["tag1", "tag2"],
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
  "title": "Updated Title",
  "metadata": {
    "key": "new_value"
  },
  "tags": ["tag1", "tag3"],
  "is_archived": true
}
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "title": "Updated Title",
  "metadata": {
    "key": "new_value"
  },
  "tags": ["tag1", "tag3"],
  "is_archived": true,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T13:00:00Z"
}
```

#### Delete a Conversation

- **URL**: `/api/v1/conversations/{conversation_id}`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Description**: Delete a conversation

**Response** (204 No Content)

### Message Endpoints

#### Get All Messages in a Conversation

- **URL**: `/api/v1/conversations/{conversation_id}/messages`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get all messages in a conversation

**Response** (200 OK):
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174001",
    "role": "user",
    "content": "Hello, I have a question about my symptoms.",
    "message_type": "text",
    "voice_url": null,
    "metadata": {},
    "created_at": "2023-01-01T12:00:00Z"
  },
  {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174001",
    "role": "assistant",
    "content": "Hello! I'm here to help. Please describe your symptoms.",
    "message_type": "text",
    "voice_url": null,
    "metadata": {},
    "created_at": "2023-01-01T12:01:00Z"
  }
]
```

#### Create a New Message

- **URL**: `/api/v1/conversations/{conversation_id}/messages`
- **Method**: `POST`
- **Auth Required**: Yes
- **Description**: Create a new message in a conversation. When a user message is created, the system will automatically generate an assistant response.

**Request Body**:
```json
{
  "role": "user",
  "content": "I've been experiencing headaches and fatigue.",
  "message_type": "text",
  "voice_url": null,
  "metadata": {}
}
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174001",
  "role": "user",
  "content": "I've been experiencing headaches and fatigue.",
  "message_type": "text",
  "voice_url": null,
  "metadata": {},
  "created_at": "2023-01-01T12:05:00Z"
}
```

### Voice Endpoints

#### Create a Voice Session

- **URL**: `/api/v1/voice/session/create`
- **Method**: `POST`
- **Auth Required**: Yes
- **Description**: Create a new voice session for real-time voice communication

**Request Body**:
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174001",
  "metadata": {
    // Optional metadata
    "instructions": "You are a helpful medical assistant.",
    "voice_settings": {
      "voice_id": "alloy",
      "temperature": 0.8,
      "max_output_tokens": 2048
    }
  }
}
```

**Response** (200 OK):
```json
{
  "id": "session_123456",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "active",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "metadata": {
    "instructions": "You are a helpful medical assistant."
  },
  "config": {
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
  },
  "created_at": "2023-01-01T12:00:00Z"
}
```

#### Get Voice Session Status

- **URL**: `/api/v1/voice/session/{session_id}/status`
- **Method**: `GET`
- **Auth Required**: Yes
- **Description**: Get the status of a voice session

**Response** (200 OK):
```json
{
  "id": "session_123456",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "active",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "metadata": {
    "instructions": "You are a helpful medical assistant."
  },
  "config": {
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
  },
  "created_at": "2023-01-01T12:00:00Z"
}
```

#### Delete a Voice Session

- **URL**: `/api/v1/voice/session/{session_id}`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Description**: Delete a voice session

**Response** (200 OK):
```json
{
  "message": "Voice session deleted"
}
```

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
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "medical_history_id": "123e4567-e89b-12d3-a456-426614174002",
  "preferences": {
    "theme": "light",
    "notifications_enabled": true
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
  "date_of_birth": "1990-01-01"
}
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "first_name": "John",
  "last_name": "Smith",
  "date_of_birth": "1990-01-01",
  "medical_history_id": "123e4567-e89b-12d3-a456-426614174002",
  "preferences": {
    "theme": "light",
    "notifications_enabled": true
  },
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T13:00:00Z"
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
  "theme": "dark",
  "notifications_enabled": false
}
```

**Response** (200 OK):
```json
{
  "theme": "dark",
  "notifications_enabled": false
}
```

## WebSocket API

The Medical Chatbot provides a WebSocket API for real-time voice communication.

### Voice WebSocket

- **URL**: `/api/v1/voice/ws/{session_id}`
- **Auth Required**: Yes (via session_id)
- **Description**: WebSocket endpoint for real-time voice communication

#### Connection

To connect to the WebSocket, you need a valid session ID obtained from the Create Voice Session endpoint.

#### Message Types

The WebSocket API supports the following message types:

##### Client to Server

1. **Audio Data**
   ```json
   {
     "type": "audio",
     "data": "base64_encoded_audio_data"
   }
   ```

2. **Text Message**
   ```json
   {
     "type": "text",
     "text": "Hello, I have a question."
   }
   ```

3. **Configuration Update**
   ```json
   {
     "type": "config",
     "config": {
       "voice_settings": {
         "voice_id": "nova",
         "stability": 0.7,
         "similarity_boost": 0.3,
         "temperature": 0.5,
         "max_output_tokens": 1024
       },
       "transcription_settings": {
         "language": "en",
         "model": "whisper-1"
       }
     }
   }
   ```

4. **Control Message**
   ```json
   {
     "type": "control",
     "action": "start" // or "stop", "pause", "resume"
   }
   ```

##### Server to Client

1. **Transcription**
   ```json
   {
     "type": "transcription",
     "text": "Hello, I have a question.",
     "is_final": true
   }
   ```

2. **Status**
   ```json
   {
     "type": "status",
     "status": "listening",
     "message": "Listening..."
   }
   ```

3. **Error**
   ```json
   {
     "type": "error",
     "message": "Error processing audio"
   }
   ```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `200 OK`: The request was successful
- `201 Created`: The resource was successfully created
- `204 No Content`: The request was successful but there is no content to return
- `400 Bad Request`: The request was invalid or cannot be served
- `401 Unauthorized`: Authentication is required or failed
- `403 Forbidden`: The request is forbidden
- `404 Not Found`: The resource could not be found
- `500 Internal Server Error`: An error occurred on the server

Error responses include a JSON object with a `detail` field that provides more information about the error:

```json
{
  "detail": "Error message"
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
  "created_at": "datetime"
}
```

### Token

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "string",
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
  "status": "string", // "active", "inactive", or "error"
  "token": "string",
  "metadata": "object",
  "config": {
    "voice_settings": {
      "voice_id": "string",
      "stability": "float",
      "similarity_boost": "float",
      "temperature": "float",
      "max_output_tokens": "integer"
    },
    "transcription_settings": {
      "language": "string",
      "model": "string"
    }
  },
  "created_at": "datetime"
}
```

### User Profile

```json
{
  "id": "UUID",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "date",
  "medical_history_id": "UUID or null",
  "preferences": "object",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Examples

### Example: Complete Conversation Flow

1. **Login**

   Request:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "securepassword"}'
   ```

   Response:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "expires_in": 3600
   }
   ```

2. **Create a Conversation**

   Request:
   ```bash
   curl -X POST http://localhost:8000/api/v1/conversations \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -d '{"title": "Medical Consultation"}'
   ```

   Response:
   ```json
   {
     "id": "123e4567-e89b-12d3-a456-426614174000",
     "user_id": "123e4567-e89b-12d3-a456-426614174001",
     "title": "Medical Consultation",
     "metadata": {},
     "tags": [],
     "is_archived": false,
     "created_at": "2023-01-01T12:00:00Z",
     "updated_at": "2023-01-01T12:00:00Z"
   }
   ```

3. **Send a Message**

   Request:
   ```bash
   curl -X POST http://localhost:8000/api/v1/conversations/123e4567-e89b-12d3-a456-426614174000/messages \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -d '{"role": "user", "content": "I have been experiencing headaches and fatigue.", "message_type": "text"}'
   ```

   Response:
   ```json
   {
     "id": "123e4567-e89b-12d3-a456-426614174002",
     "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
     "role": "user",
     "content": "I have been experiencing headaches and fatigue.",
     "message_type": "text",
     "voice_url": null,
     "metadata": {},
     "created_at": "2023-01-01T12:05:00Z"
   }
   ```

4. **Get Messages**

   Request:
   ```bash
   curl -X GET http://localhost:8000/api/v1/conversations/123e4567-e89b-12d3-a456-426614174000/messages \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

   Response:
   ```json
   [
     {
       "id": "123e4567-e89b-12d3-a456-426614174002",
       "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
       "role": "user",
       "content": "I have been experiencing headaches and fatigue.",
       "message_type": "text",
       "voice_url": null,
       "metadata": {},
       "created_at": "2023-01-01T12:05:00Z"
     },
     {
       "id": "123e4567-e89b-12d3-a456-426614174003",
       "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
       "role": "assistant",
       "content": "I'm sorry to hear that you're experiencing headaches and fatigue. These symptoms can be caused by various factors. Could you provide more details about your symptoms? For example, how long have you been experiencing them, how severe are they, and are there any other symptoms you've noticed?",
       "message_type": "text",
       "voice_url": null,
       "metadata": {},
       "created_at": "2023-01-01T12:05:05Z"
     }
   ]
   ```

### Example: Voice Session

1. **Create a Voice Session**

   Request:
   ```bash
   curl -X POST http://localhost:8000/api/v1/voice/session/create \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -d '{"conversation_id": "123e4567-e89b-12d3-a456-426614174000"}'
   ```

   Response:
   ```json
   {
     "id": "session_123456",
     "user_id": "123e4567-e89b-12d3-a456-426614174001",
     "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
     "status": "active",
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "metadata": {},
     "config": {
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
     },
     "created_at": "2023-01-01T12:10:00Z"
   }
   ```

2. **Connect to WebSocket**

   Use the session ID to connect to the WebSocket:
   ```javascript
   const socket = new WebSocket(`ws://localhost:8000/api/v1/voice/ws/session_123456`);
   
   socket.onopen = () => {
     console.log('Connected to WebSocket');
     
     // Start the conversation
     socket.send(JSON.stringify({
       type: 'control',
       action: 'start'
     }));
   };
   
   socket.onmessage = (event) => {
     const message = JSON.parse(event.data);
     console.log('Received message:', message);
     
     // Handle different message types
     switch (message.type) {
       case 'transcription':
         console.log('Transcription:', message.text);
         break;
       case 'status':
         console.log('Status:', message.status, message.message);
         break;
       case 'error':
         console.error('Error:', message.message);
         break;
     }
   };
   
   // Send audio data
   function sendAudioData(audioData) {
     socket.send(JSON.stringify({
       type: 'audio',
       data: audioData
     }));
   }
   ```

3. **Delete the Voice Session**

   Request:
   ```bash
   curl -X DELETE http://localhost:8000/api/v1/voice/session/session_123456 \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

   Response:
   ```json
   {
     "message": "Voice session deleted"
   }
   ```
