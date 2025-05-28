import { useState, useEffect, useCallback, useRef } from 'react'
import { VoiceSessionAPI } from '@/lib/voice-session-api'
import { LIVEKIT_CONFIG } from '@/lib/livekit-config'
import {
  VoiceSession,
  CreateVoiceSessionRequest,
  VoiceSessionStatus,
  VoiceSessionError
} from '@/types/voice'

export interface UseVoiceSessionOptions {
  conversationId?: string
  autoConnect?: boolean
  onError?: (error: VoiceSessionError) => void
  onStatusChange?: (status: string) => void
}

export interface UseVoiceSessionReturn {
  // Session state
  session: VoiceSession | null
  status: VoiceSessionStatus | null
  isConnecting: boolean
  error: VoiceSessionError | null

  // LiveKit connection info
  livekitUrl: string
  livekitToken: string | null

  // Actions
  startSession: (conversationId?: string) => Promise<void>
  endSession: () => Promise<void>

  // Utilities
  clearError: () => void
}

export function useVoiceSession(options: UseVoiceSessionOptions = {}): UseVoiceSessionReturn {
  const {
    conversationId: initialConversationId,
    autoConnect = false,
    onError,
    onStatusChange,
  } = options

  // State
  const [session, setSession] = useState<VoiceSession | null>(null)
  const [status, setStatus] = useState<VoiceSessionStatus | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<VoiceSessionError | null>(null)

  // LiveKit connection info (stored separately since it comes from top-level response)
  const [livekitInfo, setLivekitInfo] = useState<{
    token: string | null
    user_id: string | null
  }>({ token: null, user_id: null })

  // Refs
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Handle error
  const handleError = useCallback((err: VoiceSessionError) => {
    console.error('Voice session error:', err)
    setError(err)
    onError?.(err)
  }, [onError])

  // Update status
  const updateStatus = useCallback(async () => {
    if (!session?.id) return

    try {
      const newStatus = await VoiceSessionAPI.getVoiceSessionStatus(session.id)
      setStatus(newStatus)
      onStatusChange?.(newStatus.status)
    } catch (err) {
      console.error('Failed to update status:', err)
    }
  }, [session?.id, onStatusChange])

  // Start session
  const startSession = useCallback(async (conversationId?: string) => {
    try {
      setIsConnecting(true)
      clearError()

      let targetConversationId = conversationId || initialConversationId

      console.log('Starting voice session with conversation ID:', targetConversationId)

      // Create conversation if none provided
      if (!targetConversationId) {
        console.log('No conversation ID provided, creating new conversation...')

        try {
          const conversation = await VoiceSessionAPI.createConversation()
          targetConversationId = conversation.id
          console.log('Created conversation with ID:', targetConversationId)
        } catch (error) {
          console.error('Failed to create conversation:', error)
          // Generate a fallback UUID if conversation creation fails
          targetConversationId = crypto.randomUUID()
          console.log('Using fallback conversation ID:', targetConversationId)
        }
      }

      const request: CreateVoiceSessionRequest = {
        conversation_id: targetConversationId,
        metadata: {
          instructions: "You are a helpful medical assistant. Provide clear, accurate medical information while being empathetic and professional."
        }
      }

      const response = await VoiceSessionAPI.createVoiceSession(request)

      // Store LiveKit connection info from top-level response
      setLivekitInfo({
        token: response.token,
        user_id: response.user_id,
      })

      setIsConnecting(false)

      // Start status polling
      statusIntervalRef.current = setInterval(updateStatus, 5000)

    } catch (err) {
      setIsConnecting(false)
      console.error('Start session error details:', err)
      if (err instanceof VoiceSessionError) {
        handleError(err)
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
        handleError(new VoiceSessionError('START_SESSION_FAILED', `Failed to start voice session: ${errorMessage}`))
      }
    }
  }, [initialConversationId, clearError, handleError, updateStatus])

  // End session
  const endSession = useCallback(async () => {
    try {
      // Clear status polling
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current)
        statusIntervalRef.current = null
      }

      // End session on backend
      if (session?.id) {
        await VoiceSessionAPI.endVoiceSession(session.id)
      }

      // Reset state
      setSession(null)
      setStatus(null)
      setLivekitInfo({ token: null, user_id: null })

    } catch (err) {
      console.error('Failed to end session:', err)
      if (err instanceof VoiceSessionError) {
        handleError(err)
      } else {
        handleError(new VoiceSessionError('END_SESSION_FAILED', 'Failed to end voice session'))
      }
    }
  }, [session?.id, handleError])

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && initialConversationId) {
      startSession(initialConversationId)
    }

    // Cleanup on unmount
    return () => {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current)
      }
    }
  }, [autoConnect, initialConversationId, startSession])

  return {
    // Session state
    session,
    status,
    isConnecting,
    error,

    // LiveKit connection info
    livekitUrl: LIVEKIT_CONFIG.url,
    livekitToken: livekitInfo.token,

    // Actions
    startSession,
    endSession,

    // Utilities
    clearError,
  }
}
