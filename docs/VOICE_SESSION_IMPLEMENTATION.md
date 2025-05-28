# Voice Session Implementation with Livekit

This document describes the implementation of voice sessions using Livekit in the Medical Chatbot frontend.

## Overview

The voice session feature allows users to have real-time voice conversations with the AI medical assistant. It uses Livekit for real-time communication and integrates with the existing backend API for session management.

## Architecture

### Components

1. **VoiceChatInterface** (`components/voice-chat-interface.tsx`)
   - Main UI component for voice interactions
   - Handles session start/stop and displays connection status
   - Shows transcriptions and error messages

2. **LivekitVoiceRoom** (`components/livekit-voice-room.tsx`)
   - Livekit room component for real-time audio communication
   - Provides voice controls (mic, speaker, end call)
   - Handles audio visualization and participant management

3. **useVoiceSession** (`hooks/use-voice-session.ts`)
   - Custom hook for voice session management
   - Handles session lifecycle (create, connect, disconnect)
   - Manages Livekit room connection and events

### API Layer

1. **VoiceSessionAPI** (`lib/voice-session-api.ts`)
   - Client-side API for voice session operations
   - Handles session creation, status checking, and termination

2. **Next.js API Routes** (`app/api/voice/session/...`)
   - Proxy routes to backend API
   - Handle authentication and error formatting

### Configuration

1. **Livekit Config** (`lib/livekit-config.ts`)
   - Configuration constants for Livekit
   - Voice settings and connection parameters

2. **Types** (`types/voice.ts`)
   - TypeScript interfaces for voice session data
   - Error handling classes

## Setup Instructions

### 1. Environment Variables

Create a `.env.local` file with the following variables:

```env
# Livekit Configuration
NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Backend API Configuration
NEXT_PUBLIC_API_URL=https://medbot-backend.fly.dev/api/v1
FLY_SERVER_URL=https://medbot-backend.fly.dev
```

### 2. Dependencies

The following packages are required:

```json
{
  "@livekit/components-react": "^2.x.x",
  "livekit-client": "^2.x.x",
  "livekit-server-sdk": "^2.x.x"
}
```

### 3. Backend Requirements

The backend must provide the following endpoints:

- `POST /api/v1/voice/session/create` - Create a new voice session
- `GET /api/v1/voice/session/{id}` - Get session details
- `GET /api/v1/voice/session/{id}/status` - Get session status
- `POST /api/v1/voice/session/{id}/end` - End a session

## Usage

### Starting a Voice Session

```typescript
import { useVoiceSession } from '@/hooks/use-voice-session'

function MyComponent() {
  const { startSession, isConnecting, isConnected, error } = useVoiceSession({
    onTranscription: (text, isFinal) => {
      console.log('Transcription:', text, 'Final:', isFinal)
    },
    onError: (error) => {
      console.error('Voice session error:', error)
    }
  })

  const handleStart = async () => {
    await startSession() // Creates conversation automatically
    // or
    await startSession('existing-conversation-id')
  }

  return (
    <div>
      <button onClick={handleStart} disabled={isConnecting}>
        {isConnecting ? 'Connecting...' : 'Start Voice Session'}
      </button>
      {error && <div>Error: {error.message}</div>}
    </div>
  )
}
```

### Using the Voice Chat Interface

```typescript
import VoiceChatInterface from '@/components/voice-chat-interface'

function ChatPage() {
  return (
    <div className="h-screen">
      <VoiceChatInterface />
    </div>
  )
}
```

## Features

### Voice Controls

- **Microphone Toggle**: Enable/disable microphone input
- **Speaker Toggle**: Control audio output
- **End Call**: Terminate the voice session

### Audio Visualization

- Real-time audio level visualization
- Connection status indicators
- Participant count display

### Transcription

- Real-time speech-to-text transcription
- Display of conversation history
- Final vs. interim transcription handling

### Error Handling

- Connection error recovery
- Session timeout handling
- User-friendly error messages

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check Livekit server URL and credentials
   - Verify network connectivity
   - Check browser permissions for microphone access

2. **Audio Issues**
   - Ensure microphone permissions are granted
   - Check audio device availability
   - Verify Livekit audio configuration

3. **Session Creation Failures**
   - Verify backend API connectivity
   - Check authentication token validity
   - Review backend logs for errors

### Debug Mode

Enable debug logging by setting:

```typescript
// In your component
useEffect(() => {
  if (process.env.NODE_ENV === 'development') {
    // Enable Livekit debug logging
    import('livekit-client').then(({ setLogLevel, LogLevel }) => {
      setLogLevel(LogLevel.debug)
    })
  }
}, [])
```

## Security Considerations

1. **Token Management**
   - Livekit tokens should be short-lived
   - Tokens are generated server-side for security

2. **Audio Privacy**
   - Audio data is processed in real-time
   - No audio is stored unless explicitly configured

3. **Authentication**
   - All API calls require valid JWT tokens
   - Session access is user-specific

## Performance Optimization

1. **Connection Management**
   - Automatic reconnection on network issues
   - Connection pooling for multiple sessions

2. **Audio Quality**
   - Adaptive bitrate based on network conditions
   - Echo cancellation and noise suppression

3. **Resource Cleanup**
   - Proper cleanup of Livekit resources
   - Memory leak prevention

## Future Enhancements

1. **Video Support**
   - Add video calling capabilities
   - Screen sharing for medical consultations

2. **Recording**
   - Session recording for review
   - Transcript generation and storage

3. **Advanced Features**
   - Multi-participant sessions
   - Real-time language translation
   - Voice activity detection improvements
