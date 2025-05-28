export interface VoiceSessionConfig {
  voice_settings: {
    voice_id: string
    stability?: number
    similarity_boost?: number
    temperature?: number
    max_output_tokens?: number
  }
  transcription_settings?: {
    language: string
    model: string
  }
}

export interface VoiceSession {
  id: string
  user_id: string
  conversation_id: string
  status: 'active' | 'inactive' | 'error'
  token: string
  metadata?: Record<string, any>
  config: VoiceSessionConfig
  created_at: string
  // Note: livekit_room_name and livekit_token are returned at the top level of CreateVoiceSessionResponse
}

export interface CreateVoiceSessionRequest {
  conversation_id: string
  metadata?: {
    instructions?: string
    voice_settings?: {
      voice_id?: string
      temperature?: number
      max_output_tokens?: number
    }
  }
}

export interface CreateVoiceSessionResponse {
  token: string
  user_id: string,
}

export interface VoiceSessionStatus {
  session_id: string
  status: 'active' | 'inactive' | 'error'
  participants_count: number
  duration: number
  last_activity: string
}

export interface LivekitConfig {
  url: string
  apiKey: string
  apiSecret: string
}

export interface VoiceMessage {
  type: 'audio' | 'text' | 'transcription' | 'status' | 'error' | 'control' | 'config'
  data?: string
  text?: string
  is_final?: boolean
  status?: string
  message?: string
  action?: 'start' | 'stop' | 'pause' | 'resume'
  config?: VoiceSessionConfig
}

export interface AudioSettings {
  sampleRate: number
  channels: number
  bitDepth: number
  echoCancellation: boolean
  noiseSuppression: boolean
  autoGainControl: boolean
}

export class VoiceSessionError extends Error {
  public code: string
  public details?: Record<string, any>

  constructor(code: string, message: string, details?: Record<string, any>) {
    super(message)
    this.name = 'VoiceSessionError'
    this.code = code
    this.details = details
  }
}
