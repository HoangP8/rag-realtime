import {
  CreateVoiceSessionRequest,
  CreateVoiceSessionResponse,
  VoiceSession,
  VoiceSessionStatus,
  VoiceSessionError
} from '@/types/voice'
import { getAuthHeaders, isAuthenticated } from '@/lib/auth-utils'

export class VoiceSessionAPI {
  private static getBackendUrl() {
    return process.env.NEXT_PUBLIC_BACKEND_URL || "https://medbot-backend.fly.dev"
  }

  static async createVoiceSession(request: CreateVoiceSessionRequest): Promise<CreateVoiceSessionResponse> {
    try {
      // Check authentication before making request
      if (!isAuthenticated()) {
        console.log('User is not authenticated or token is expired')
        throw new VoiceSessionError(
          'AUTHENTICATION_REQUIRED',
          'User is not authenticated or token is expired'
        )
      }

      const backendUrl = this.getBackendUrl()
      const url = `${backendUrl}/api/v1/voice/session/create`
      const headers = getAuthHeaders()
      const body = JSON.stringify(request)

      const response = await fetch(url, {
        method: "POST",
        headers,
        body,
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', Object.fromEntries(response.headers.entries()))

      const data = await response.json()
      console.log('Response data:', data)

      if (!response.ok) {
        throw new VoiceSessionError(
          data.error_code || 'CREATE_SESSION_FAILED',
          data.message || data.error || "Failed to create voice session",
          data.details
        )
      }

      return data
    } catch (error) {
      console.error("Create voice session error:", error)
      if (error instanceof VoiceSessionError) {
        throw error
      }
      throw new VoiceSessionError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : "Network error occurred",
        { originalError: error }
      )
    }
  }

  static async getVoiceSession(sessionId: string): Promise<VoiceSession> {
    try {
      const backendUrl = this.getBackendUrl()
      const response = await fetch(`${backendUrl}/api/v1/voice/session/${sessionId}`, {
        method: "GET",
        headers: getAuthHeaders(),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new VoiceSessionError(
          data.error_code || 'GET_SESSION_FAILED',
          data.message || data.error || "Failed to get voice session",
          data.details
        )
      }

      return data.session
    } catch (error) {
      console.error("Get voice session error:", error)
      if (error instanceof VoiceSessionError) {
        throw error
      }
      throw new VoiceSessionError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : "Network error occurred",
        { originalError: error }
      )
    }
  }

  static async getVoiceSessionStatus(sessionId: string): Promise<VoiceSessionStatus> {
    try {
      const backendUrl = this.getBackendUrl()
      const response = await fetch(`${backendUrl}/api/v1/voice/session/${sessionId}/status`, {
        method: "GET",
        headers: getAuthHeaders(),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new VoiceSessionError(
          data.error_code || 'GET_STATUS_FAILED',
          data.message || data.error || "Failed to get voice session status",
          data.details
        )
      }

      return data
    } catch (error) {
      console.error("Get voice session status error:", error)
      if (error instanceof VoiceSessionError) {
        throw error
      }
      throw new VoiceSessionError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : "Network error occurred",
        { originalError: error }
      )
    }
  }

  static async endVoiceSession(sessionId: string): Promise<void> {
    try {
      const backendUrl = this.getBackendUrl()
      const response = await fetch(`${backendUrl}/api/v1/voice/session/${sessionId}/end`, {
        method: "POST",
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new VoiceSessionError(
          data.error_code || 'END_SESSION_FAILED',
          data.message || data.error || "Failed to end voice session",
          data.details
        )
      }
    } catch (error) {
      console.error("End voice session error:", error)
      if (error instanceof VoiceSessionError) {
        throw error
      }
      throw new VoiceSessionError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : "Network error occurred",
        { originalError: error }
      )
    }
  }

  static async updateVoiceSessionConfig(sessionId: string, config: any): Promise<VoiceSession> {
    try {
      const backendUrl = this.getBackendUrl()
      const response = await fetch(`${backendUrl}/api/v1/voice/session/${sessionId}/config`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify({ config }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new VoiceSessionError(
          data.error_code || 'UPDATE_CONFIG_FAILED',
          data.message || data.error || "Failed to update voice session config",
          data.details
        )
      }

      return data.session
    } catch (error) {
      console.error("Update voice session config error:", error)
      if (error instanceof VoiceSessionError) {
        throw error
      }
      throw new VoiceSessionError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : "Network error occurred",
        { originalError: error }
      )
    }
  }

  static async createConversation(title?: string): Promise<{ id: string }> {
    try {
      // Check authentication before making request
      if (!isAuthenticated()) {
        throw new VoiceSessionError(
          'AUTHENTICATION_REQUIRED',
          'User is not authenticated or token is expired'
        )
      }

      // Call backend API directly
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "https://medbot-backend.fly.dev"
      const apiUrl = `${backendUrl}/api/v1/conversations/`

      console.log('Creating conversation with URL:', apiUrl)

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          title: title || `Voice Consultation - ${new Date().toLocaleString()}`,
          metadata: {},
          tags: ["voice", "consultation"]
        }),
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', Object.fromEntries(response.headers.entries()))

      // Check if response is actually JSON
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text()
        console.error('Non-JSON response received:', textResponse)
        throw new VoiceSessionError(
          'INVALID_RESPONSE',
          `Server returned non-JSON response: ${textResponse.substring(0, 200)}...`,
          { status: response.status, contentType, response: textResponse }
        )
      }

      const data = await response.json()
      console.log('Response data:', data)

      if (!response.ok) {
        throw new VoiceSessionError(
          data.error_code || 'CREATE_CONVERSATION_FAILED',
          data.message || data.error || "Failed to create conversation",
          data.details
        )
      }

      // The backend might return the conversation in different formats
      // Handle both { id: "..." } and { conversation: { id: "..." } }
      return {
        id: data.id || data.conversation?.id || data.conversation_id
      }
    } catch (error) {
      console.error("Create conversation error:", error)
      if (error instanceof VoiceSessionError) {
        throw error
      }
      throw new VoiceSessionError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : "Network error occurred",
        { originalError: error }
      )
    }
  }

  static async saveVoiceTranscription(conversationId: string, messages: Array<{
    role: 'user' | 'assistant',
    content: string,
    timestamp: Date
  }>): Promise<boolean> {
    try {
      if (!isAuthenticated()) {
        throw new VoiceSessionError(
          'AUTHENTICATION_REQUIRED',
          'User is not authenticated or token is expired'
        )
      }

      const backendUrl = this.getBackendUrl()
      const url = `${backendUrl}/api/v1/conversations/${conversationId}/messages/batch`
      
      // Format messages for the API
      const formattedMessages = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        message_type: "voice_transcription",
        metadata: {
          timestamp: msg.timestamp.toISOString(),
          source: "livekit_transcription"
        }
      }));
      
      const response = await fetch(url, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ messages: formattedMessages }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new VoiceSessionError(
          data.error_code || 'SAVE_TRANSCRIPTION_FAILED',
          data.message || data.error || "Failed to save voice transcription",
          data.details
        )
      }

      return true
    } catch (error) {
      console.error("Save voice transcription error:", error)
      if (error instanceof VoiceSessionError) {
        throw error
      }
      throw new VoiceSessionError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : "Network error occurred",
        { originalError: error }
      )
    }
  }
}
