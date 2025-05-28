import { LivekitConfig, AudioSettings } from '@/types/voice'

export const LIVEKIT_CONFIG: LivekitConfig = {
  url: process.env.NEXT_PUBLIC_LIVEKIT_URL || 'wss://medbot-livekit.livekit.cloud',
  apiKey: process.env.LIVEKIT_API_KEY || '',
  apiSecret: process.env.LIVEKIT_API_SECRET || '',
}

export const DEFAULT_AUDIO_SETTINGS: AudioSettings = {
  sampleRate: 16000,
  channels: 1,
  bitDepth: 16,
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
}

export const VOICE_SETTINGS = {
  DEFAULT_VOICE_ID: 'alloy',
  AVAILABLE_VOICES: [
    { id: 'alloy', name: 'Alloy', description: 'Neutral, balanced voice' },
    { id: 'echo', name: 'Echo', description: 'Warm, friendly voice' },
    { id: 'fable', name: 'Fable', description: 'Expressive, storytelling voice' },
    { id: 'onyx', name: 'Onyx', description: 'Deep, authoritative voice' },
    { id: 'nova', name: 'Nova', description: 'Bright, energetic voice' },
    { id: 'shimmer', name: 'Shimmer', description: 'Gentle, soothing voice' },
  ],
  DEFAULT_TEMPERATURE: 0.8,
  DEFAULT_MAX_OUTPUT_TOKENS: 2048,
  DEFAULT_STABILITY: 0.7,
  DEFAULT_SIMILARITY_BOOST: 0.3,
}

export const TRANSCRIPTION_SETTINGS = {
  DEFAULT_LANGUAGE: 'en',
  DEFAULT_MODEL: 'whisper-1',
  SUPPORTED_LANGUAGES: [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'ru', name: 'Russian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'zh', name: 'Chinese' },
  ],
}

export const CONNECTION_CONFIG = {
  RECONNECT_ATTEMPTS: 3,
  RECONNECT_DELAY: 2000,
  CONNECTION_TIMEOUT: 10000,
  HEARTBEAT_INTERVAL: 30000,
}

export const ROOM_CONFIG = {
  ADAPTIVE_STREAM: true,
  DYNACAST: true,
  VIDEO_CAPTURE_DEFAULTS: {
    resolution: {
      width: 640,
      height: 480,
    },
    frameRate: 15,
  },
  AUDIO_CAPTURE_DEFAULTS: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    sampleRate: 16000,
    channelCount: 1,
  },
}

export function validateLivekitConfig(): boolean {
  const errors: string[] = []

  if (!LIVEKIT_CONFIG.url) {
    errors.push('NEXT_PUBLIC_LIVEKIT_URL is not configured')
  }

  // Only validate server-side credentials on the server
  if (typeof window === 'undefined') {
    if (!LIVEKIT_CONFIG.apiKey) {
      errors.push('LIVEKIT_API_KEY is not configured')
    }

    if (!LIVEKIT_CONFIG.apiSecret) {
      errors.push('LIVEKIT_API_SECRET is not configured')
    }
  }

  if (errors.length > 0) {
    console.error('Livekit configuration errors:', errors)
    return false
  }

  return true
}

export function getLivekitUrl(): string {
  return LIVEKIT_CONFIG.url
}

export function isLivekitConfigured(): boolean {
  return !!(LIVEKIT_CONFIG.url && LIVEKIT_CONFIG.apiKey && LIVEKIT_CONFIG.apiSecret)
}
