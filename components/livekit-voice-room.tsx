"use client"

import { useEffect, useState } from 'react'
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useLocalParticipant,
  useTracks,
  useRoomContext,
  useParticipants
} from '@livekit/components-react'
import { Track, Room, RoomEvent, ConnectionState } from 'livekit-client'
import { Button } from '@/components/ui/button'
import { Mic, MicOff, Volume2, VolumeX, Phone, PhoneOff } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LivekitVoiceRoomProps {
  token: string
  serverUrl: string
  roomName: string
  onConnected?: () => void
  onDisconnected?: () => void
  onError?: (error: Error) => void
  onTranscription?: (text: string, isFinal: boolean) => void
  className?: string
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
  const tracks = useTracks([Track.Source.Microphone], { onlySubscribed: false })
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

function RoomContent({
  onConnected,
  onDisconnected,
  onError,
  onEndCall
}: {
  onConnected?: () => void
  onDisconnected?: () => void
  onError?: (error: Error) => void
  onEndCall?: () => void
}) {
  const room = useRoomContext()
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    if (!room) return

    const handleConnected = () => {
      console.log('Connected to Livekit room')
      setIsConnected(true)
      onConnected?.()
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
    }
  }, [room, onConnected, onDisconnected, onError])

  if (!isConnected) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-lg text-gray-600">Connecting to voice session...</p>
      </div>
    )
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
  className
}: LivekitVoiceRoomProps) {
  const [connectionError, setConnectionError] = useState<string | null>(null)

  const handleError = (error: Error) => {
    console.error('Livekit connection error:', error)
    setConnectionError(error.message)
    onError?.(error)
  }

  const handleEndCall = () => {
    onDisconnected?.()
  }

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
        />
      </LiveKitRoom>
    </div>
  )
}
