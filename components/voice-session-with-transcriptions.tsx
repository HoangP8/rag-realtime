"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import LivekitVoiceRoom from '@/components/livekit-voice-room'
import { VoiceSessionAPI } from '@/lib/voice-session-api'

interface VoiceSessionWithTranscriptionsProps {
  conversationId: string
  onEndSession?: () => void
}

export default function VoiceSessionWithTranscriptions({
  conversationId,
  onEndSession
}: VoiceSessionWithTranscriptionsProps) {
  const [voiceSession, setVoiceSession] = useState<{
    token: string
    serverUrl: string
    roomName: string
  } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showTranscriptions, setShowTranscriptions] = useState(true)

  const startVoiceSession = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Create voice session
      const response = await VoiceSessionAPI.createVoiceSession({
        conversation_id: conversationId,
        metadata: {
          instructions: "You are a helpful medical assistant. Provide clear, accurate medical information while being empathetic and professional."
        }
      })

      if (!response || !response.token) {
        throw new Error('Invalid response from voice session API')
      }

      // Set up the voice session
      setVoiceSession({
        token: response.token,
        serverUrl: process.env.NEXT_PUBLIC_LIVEKIT_URL || "wss://medbot-livekit.fly.dev",
        roomName: `voice-session-${conversationId}`
      })
    } catch (err) {
      console.error('Failed to start voice session:', err)
      setError(err instanceof Error ? err.message : 'Failed to start voice session')
    } finally {
      setIsLoading(false)
    }
  }

  const handleEndSession = () => {
    setVoiceSession(null)
    onEndSession?.()
  }

  const handleTranscription = (text: string, isFinal: boolean, role?: 'user' | 'assistant') => {
    console.log(`[VoiceSessionWithTranscriptions] Transcription received:`, {
      text,
      isFinal,
      role,
      timestamp: new Date().toISOString()
    })
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold text-red-600">Error</h3>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
        <Button onClick={() => setError(null)} variant="outline">
          Try Again
        </Button>
      </div>
    )
  }

  if (!voiceSession) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-xl font-semibold">Voice Consultation</h2>
          <p className="text-gray-600">Start a voice conversation with your medical assistant</p>
        </div>

        <Button
          onClick={startVoiceSession}
          disabled={isLoading}
          size="lg"
          className="px-8"
        >
          {isLoading ? 'Starting...' : 'Start Voice Session'}
        </Button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header with controls */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold">Voice Consultation</h2>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTranscriptions(!showTranscriptions)}
          >
            {showTranscriptions ? 'Hide' : 'Show'} Transcriptions
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleEndSession}
          >
            End Session
          </Button>
        </div>
      </div>

      {/* Voice Room */}
      <div className="flex-1">
        <LivekitVoiceRoom
          token={voiceSession.token}
          serverUrl={voiceSession.serverUrl}
          roomName={voiceSession.roomName}
          onConnected={() => console.log('Voice session connected')}
          onDisconnected={handleEndSession}
          onError={(error) => setError(error.message)}
          onTranscription={handleTranscription}
          showTranscriptions={showTranscriptions}
          className="h-full"
        />
      </div>
    </div>
  )
}
