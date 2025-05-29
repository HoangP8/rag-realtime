"use client"

import { useEffect, useState } from 'react'
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useLocalParticipant,
  useRoomContext,
  useParticipants
} from '@livekit/components-react'
import { RoomEvent, ConnectionState } from 'livekit-client'
import { Button } from '@/components/ui/button'
import { Mic, MicOff, Volume2, VolumeX, PhoneOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import { VoiceSessionAPI } from '@/lib/voice-session-api'

interface TranscriptionMessage {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
  isFinal: boolean
}

interface LivekitVoiceRoomProps {
  token: string
  serverUrl: string
  roomName: string
  onConnected?: () => void
  onDisconnected?: (transcriptions?: Array<{
    role: 'user' | 'assistant',
    content: string,
    timestamp: Date
  }>) => void
  onError?: (error: Error) => void
  onTranscription?: (text: string, isFinal: boolean, role?: 'user' | 'assistant') => void
  className?: string
  showTranscriptions?: boolean
}

function VoiceControls({
  onEndCall,
  className
}: {
  onEndCall?: () => void
  className?: string
}) {
  const { localParticipant } = useLocalParticipant()
  const [isMicEnabled, setIsMicEnabled] = useState(true)
  const [isSpeakerEnabled, setIsSpeakerEnabled] = useState(true)

  const toggleMicrophone = async () => {
    if (localParticipant) {
      const enabled = !isMicEnabled
      await localParticipant.setMicrophoneEnabled(enabled)
      setIsMicEnabled(enabled)
    }
  }

  const toggleSpeaker = () => {
    setIsSpeakerEnabled(!isSpeakerEnabled)
    // Note: Actual speaker control implementation may vary
  }

  return (
    <div className={cn("flex items-center justify-center gap-4", className)}>
      <Button
        onClick={toggleMicrophone}
        size="lg"
        variant={isMicEnabled ? "default" : "destructive"}
        className="w-14 h-14 rounded-full"
      >
        {isMicEnabled ? (
          <Mic className="h-6 w-6" />
        ) : (
          <MicOff className="h-6 w-6" />
        )}
      </Button>

      <Button
        onClick={toggleSpeaker}
        size="lg"
        variant={isSpeakerEnabled ? "default" : "secondary"}
        className="w-14 h-14 rounded-full"
      >
        {isSpeakerEnabled ? (
          <Volume2 className="h-6 w-6" />
        ) : (
          <VolumeX className="h-6 w-6" />
        )}
      </Button>

      <Button
        onClick={onEndCall}
        size="lg"
        variant="destructive"
        className="w-14 h-14 rounded-full"
      >
        <PhoneOff className="h-6 w-6" />
      </Button>
    </div>
  )
}

function ParticipantInfo() {
  const participants = useParticipants()
  const room = useRoomContext()

  return (
    <div className="text-center space-y-2">
      <p className="text-sm text-gray-600">
        Connected to: {room?.name || 'Voice Session'}
      </p>
      <p className="text-xs text-gray-500">
        {participants.length} participant{participants.length !== 1 ? 's' : ''} in session
      </p>
    </div>
  )
}

function AudioVisualizer() {
  const [audioLevel, setAudioLevel] = useState(0)

  useEffect(() => {
    // Simple audio level visualization
    const interval = setInterval(() => {
      // This is a placeholder - actual audio level detection would require
      // access to the audio track's audio context
      setAudioLevel(Math.random() * 100)
    }, 100)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-center justify-center space-x-1">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className={cn(
            "w-2 h-8 bg-blue-200 rounded-full transition-all duration-150",
            audioLevel > (i + 1) * 20 && "bg-blue-500 scale-110"
          )}
        />
      ))}
    </div>
  )
}

function TranscriptionDisplay({
  transcriptions,
  className
}: {
  transcriptions: TranscriptionMessage[]
  className?: string
}) {
  const formatTime = (date: Date) => {
    // Use a more stable time formatting to avoid hydration issues
    try {
      return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }).format(date)
    } catch (error) {
      // Fallback for hydration issues
      return date.toLocaleTimeString()
    }
  }

  console.log('TranscriptionDisplay rendering with', transcriptions.length, 'transcriptions:', transcriptions)

  if (transcriptions.length === 0) {
    return (
      <div className={cn("flex items-center justify-center h-32 text-gray-500", className)}>
        <p className="text-sm">Transcriptions will appear here during the conversation...</p>
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col space-y-3 p-4 max-h-64 overflow-y-auto", className)}>
      <div className="text-xs text-gray-500 mb-2">
        {transcriptions.length} message{transcriptions.length !== 1 ? 's' : ''}
      </div>
      {transcriptions.map((message) => (
        <div
          key={message.id}
          className={cn(
            "flex flex-col max-w-xs rounded-lg px-3 py-2 text-sm",
            message.isUser
              ? "self-end bg-blue-500 text-white"
              : "self-start bg-gray-200 text-gray-900",
            !message.isFinal && "opacity-70 italic"
          )}
        >
          <p className="break-words">{message.text}</p>
          <span className={cn(
            "text-xs mt-1",
            message.isUser ? "text-blue-100" : "text-gray-500"
          )}>
            {formatTime(message.timestamp)} {!message.isFinal && '(interim)'}
          </span>
        </div>
      ))}
    </div>
  )
}

function RoomContent({
  onConnected,
  onDisconnected,
  onError,
  onEndCall,
  onTranscription,
  showTranscriptions = false
}: {
  onConnected?: () => void
  onDisconnected?: () => void
  onError?: (error: Error) => void
  onEndCall?: () => void
  onTranscription?: (text: string, isFinal: boolean, isUser: boolean) => void
  showTranscriptions?: boolean
}) {
  const room = useRoomContext()
  const [isConnected, setIsConnected] = useState(false)
  const [transcriptions, setTranscriptions] = useState<TranscriptionMessage[]>([])
  const [currentTranscriptions, setCurrentTranscriptions] = useState<Map<string, TranscriptionMessage>>(new Map())

  // Add test transcription for debugging
  const addTestTranscription = () => {
    const testMessage: TranscriptionMessage = {
      id: `test-${Date.now()}`,
      text: `Test transcription at ${new Date().toLocaleTimeString()}`,
      isUser: Math.random() > 0.5,
      timestamp: new Date(),
      isFinal: true
    };
    console.log('Adding test transcription:', testMessage);
    setTranscriptions(prev => [...prev, testMessage]);
  }

  useEffect(() => {
    if (!room) return

    const handleConnected = () => {
      console.log('Connected to Livekit room')
      setIsConnected(true)
      onConnected?.()

      // Register transcription handler when connected
      room.registerTextStreamHandler('lk.transcription', async (reader, participantInfo) => {
        try {
          const message = await reader.readAll();
          const attributes = reader.info.attributes;
          const isTranscription = attributes && attributes['lk.transcribed_track_id'];

          console.log('Text stream received:', {
            message,
            attributes,
            isTranscription,
            participantIdentity: participantInfo.identity,
            localIdentity: room.localParticipant.identity
          });

          if (isTranscription) {
            console.log(`New transcription from ${participantInfo.identity}: ${message}`);

            // Determine if this is from the user or the assistant
            const isUser = participantInfo.identity === room.localParticipant.identity;
            const isFinal = attributes && attributes['lk.is_final'] === 'true';

            // Create unique ID for this transcription
            const transcriptionId = `${participantInfo.identity}-${Date.now()}-${Math.random()}`;

            // Create transcription message
            const transcriptionMessage: TranscriptionMessage = {
              id: transcriptionId,
              text: message,
              isUser,
              timestamp: new Date(),
              isFinal: isFinal || false
            };

            console.log('Created transcription message:', transcriptionMessage);

            if (isFinal) {
              console.log('Adding final transcription to state');
              // Add final transcription to the list
              setTranscriptions(prev => {
                const newTranscriptions = [...prev, transcriptionMessage];
                console.log('Updated transcriptions state:', newTranscriptions);
                return newTranscriptions;
              });
              // Remove from current transcriptions map
              setCurrentTranscriptions(prev => {
                const newMap = new Map(prev);
                newMap.delete(transcriptionId);
                console.log('Updated current transcriptions:', Array.from(newMap.values()));
                return newMap;
              });
            } else {
              console.log('Adding interim transcription to current state');
              // Update current transcriptions for real-time display
              setCurrentTranscriptions(prev => {
                const newMap = new Map(prev);
                newMap.set(transcriptionId, transcriptionMessage);
                console.log('Updated current transcriptions:', Array.from(newMap.values()));
                return newMap;
              });
            }

            // Pass to parent component
            onTranscription?.(message, isFinal || false, isUser);
          } else {
            console.log(`New non-transcription message from ${participantInfo.identity}: ${message}`);
          }
        } catch (error) {
          console.error('Error processing text stream:', error);
        }
      });
    }

    const handleDisconnected = () => {
      console.log('Disconnected from Livekit room')
      setIsConnected(false)
      onDisconnected?.()
    }

    const handleError = (error: Error) => {
      console.error('Livekit room error:', error)
      onError?.(error)
    }

    room.on(RoomEvent.Connected, handleConnected)
    room.on(RoomEvent.Disconnected, handleDisconnected)
    room.on(RoomEvent.ConnectionStateChanged, (state: ConnectionState) => {
      if (state === ConnectionState.Disconnected) {
        handleError(new Error('Connection failed'))
      }
    })

    return () => {
      room.off(RoomEvent.Connected, handleConnected)
      room.off(RoomEvent.Disconnected, handleDisconnected)
      // Unregister text stream handler
      room.unregisterTextStreamHandler('lk.transcription');
    }
  }, [room, onConnected, onDisconnected, onError, onTranscription])

  if (!isConnected) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-lg text-gray-600">Connecting to voice session...</p>
      </div>
    )
  }

  // Combine final transcriptions with current ones for display
  const allTranscriptions = [
    ...transcriptions,
    ...Array.from(currentTranscriptions.values())
  ].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

  console.log('RoomContent render:', {
    showTranscriptions,
    transcriptionsCount: transcriptions.length,
    currentTranscriptionsCount: currentTranscriptions.size,
    allTranscriptionsCount: allTranscriptions.length,
    isConnected
  });

  if (showTranscriptions) {
    return (
      <div className="flex flex-col h-full">
        {/* Header with connection status */}
        <div className="flex-shrink-0 p-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <ParticipantInfo />
            {/* Debug button - remove in production */}
            <Button
              onClick={addTestTranscription}
              variant="outline"
              size="sm"
              className="text-xs"
            >
              Add Test Message
            </Button>
          </div>
        </div>

        {/* Transcription Display */}
        <div className="flex-1 overflow-hidden">
          <TranscriptionDisplay
            transcriptions={allTranscriptions}
            className="h-full"
          />
        </div>

        {/* Voice Controls */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200">
          <VoiceControls onEndCall={onEndCall} />
        </div>

        {/* Audio Renderer - handles playback of remote audio */}
        <RoomAudioRenderer />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full space-y-8">
      {/* Connection Status */}
      <ParticipantInfo />

      {/* Audio Visualizer */}
      <div className="space-y-4">
        <p className="text-center text-sm text-gray-600">Voice Activity</p>
        <AudioVisualizer />
      </div>

      {/* Voice Controls */}
      <VoiceControls onEndCall={onEndCall} />

      {/* Audio Renderer - handles playback of remote audio */}
      <RoomAudioRenderer />
    </div>
  )
}

export default function LivekitVoiceRoom({
  token,
  serverUrl,
  roomName,
  onConnected,
  onDisconnected,
  onError,
  onTranscription,
  className,
  showTranscriptions = false
}: LivekitVoiceRoomProps) {
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [transcriptionData, setTranscriptionData] = useState<Array<{
    text: string,
    isUser: boolean,
    timestamp: Date
  }>>([])

  const handleError = (error: Error) => {
    console.error('Livekit connection error:', error)
    setConnectionError(error.message)
    onError?.(error)
  }

  const handleEndCall = () => {
    onDisconnected?.()
  }

  const handleTranscription = (text: string, isFinal: boolean, isUser: boolean) => {
    if (isFinal) {
      // Store transcription data locally
      const newTranscription = {
        text,
        isUser,
        timestamp: new Date()
      };
      setTranscriptionData(prev => [...prev, newTranscription]);

      // Pass to parent component with role information
      onTranscription?.(text, isFinal, isUser ? 'user' : 'assistant');
    }
  }

  // Save transcriptions when disconnected
  useEffect(() => {
    return () => {
      if (transcriptionData.length > 0) {
        // Extract conversation ID from roomName (assuming format "voice-session-{conversationId}")
        const conversationId = roomName.startsWith('voice-session-')
          ? roomName.substring('voice-session-'.length)
          : null;

        if (conversationId) {
          // Format transcriptions for API
          const messages = transcriptionData.map(item => ({
            role: (item.isUser ? 'user' : 'assistant') as 'user' | 'assistant',
            content: item.text,
            timestamp: item.timestamp
          }));

          // Save to backend
          VoiceSessionAPI.saveVoiceTranscription(conversationId, messages)
            .then(() => console.log('Transcriptions saved successfully'))
            .catch(err => console.error('Failed to save transcriptions:', err));
        }
      }
    };
  }, [transcriptionData, roomName]);

  if (connectionError) {
    return (
      <div className={cn("flex flex-col items-center justify-center h-full space-y-4", className)}>
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold text-red-600">Connection Error</h3>
          <p className="text-sm text-gray-600">{connectionError}</p>
        </div>
        <Button
          onClick={() => setConnectionError(null)}
          variant="outline"
        >
          Try Again
        </Button>
      </div>
    )
  }

  return (
    <div className={cn("h-full", className)}>
      <LiveKitRoom
        token={token}
        serverUrl={serverUrl}
        connect={true}
        audio={true}
        video={false}
        onError={handleError}
        options={{
          adaptiveStream: true,
          dynacast: true,
          publishDefaults: {
            audioPreset: {
              maxBitrate: 64000,
              priority: 'high',
            },
          },
        }}
      >
        <RoomContent
          onConnected={onConnected}
          onDisconnected={onDisconnected}
          onError={onError}
          onEndCall={handleEndCall}
          onTranscription={handleTranscription}
          showTranscriptions={showTranscriptions}
        />
      </LiveKitRoom>
    </div>
  )
}
