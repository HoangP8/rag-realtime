"use client"

import { AnimatePresence, motion } from "framer-motion"
import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  AgentState,
  DisconnectButton,
} from "@livekit/components-react"
import { useCallback, useEffect, useState } from "react"
import { MediaDeviceFailure } from "livekit-client"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Phone, Loader2, Shield } from "lucide-react"
import { toast } from "sonner"
import { isAuthenticated } from "@/lib/auth-utils"
import { NoAgentNotification } from "@/components/ui/NoAgentNotification"
import { CloseIcon } from "@/components/ui/CloseIcon"
import { VoiceSessionAPI } from "@/lib/voice-session-api"

interface ConnectionDetails {
  serverUrl: string
  participantToken: string
  participantName: string
  roomName: string
}

interface VoiceChatInterfaceProps {
  conversationId?: string | null
}

export default function VoiceChatInterface({ conversationId }: VoiceChatInterfaceProps) {
  const [connectionDetails, updateConnectionDetails] = useState<
    ConnectionDetails | undefined
  >(undefined)
  const [agentState, setAgentState] = useState<AgentState>("disconnected")
  const [userAuthenticated, setUserAuthenticated] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  // Add these state variables to track voice session content
  const [voiceSessionMessages, setVoiceSessionMessages] = useState<Array<{
    role: 'user' | 'assistant',
    content: string,
    timestamp: Date
  }>>([])
  const [showTextMessages, setShowTextMessages] = useState(false)

  // Check authentication status
  useEffect(() => {
    const checkAuth = () => {
      const authenticated = isAuthenticated()
      console.log('Authentication check:', authenticated)
      setUserAuthenticated(authenticated)
      
      // If token exists but is invalid, show a more specific message
      if (!authenticated && localStorage.getItem('access_token')) {
        toast.error('Your session has expired. Please log in again.')
      }
    }

    checkAuth()
    // Check auth status periodically
    const interval = setInterval(checkAuth, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [])

  const onConnectButtonClicked = useCallback(async () => {
    if (!userAuthenticated) {
      toast.error('Please log in to start a voice session')
      return
    }

    try {
      setIsConnecting(true)

      let targetConversationId = conversationId

      // If no conversationId provided, create a new conversation first
      if (!targetConversationId) {
        console.log('Creating new conversation...')
        const conversation = await VoiceSessionAPI.createConversation("Voice Consultation")
        targetConversationId = conversation.id
        console.log('Created conversation with ID:', targetConversationId)
      }

      // Create voice session using the conversation ID
      console.log('Creating voice session for conversation:', targetConversationId)
      const voiceSessionResponse = await VoiceSessionAPI.createVoiceSession({
        conversation_id: targetConversationId,
        metadata: {
          instructions: "You are a helpful medical assistant. Provide clear, accurate medical information while being empathetic and professional."
        }
      })

      console.log('Voice session response:', voiceSessionResponse)
      
      if (!voiceSessionResponse || !voiceSessionResponse.token) {
        throw new Error('Invalid response from voice session API')
      }

      // Make sure to use the correct LiveKit URL from environment variables
      const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || 'wss://clinical-chatbot-1dewlazs.livekit.cloud';

      // Update connection details with the voice session response
      updateConnectionDetails({
        participantToken: voiceSessionResponse.token,
        serverUrl: serverUrl, // Use the variable defined above
        participantName: voiceSessionResponse.user_id,
        roomName: `voice-session-${targetConversationId}`
      })

      console.log('Voice session created successfully')
    } catch (error) {
      console.error('Failed to create voice session:', error)
      toast.error('Failed to connect to voice session: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setIsConnecting(false)
    }
  }, [userAuthenticated, conversationId])

  const onDeviceFailure = useCallback((error?: MediaDeviceFailure) => {
    console.error(error)
    alert(
      "Error acquiring camera or microphone permissions. Please make sure you grant the necessary permissions in your browser and reload the tab"
    )
  }, [])

  // Add this function to handle session end
  const handleVoiceSessionEnd = useCallback(() => {
    // Reset connection details to end the LiveKit session
    updateConnectionDetails(undefined)
    // Show the text message view with the voice session content
    setShowTextMessages(true)
  }, [])

  // Add a function to handle transcriptions
  const handleTranscription = useCallback((text: string, role: 'user' | 'assistant') => {
    setVoiceSessionMessages(prev => [...prev, {
      role,
      content: text,
      timestamp: new Date()
    }]);
  }, []);

  if (connectionDetails) {
    return (
      <main
        data-lk-theme="default"
        className="h-full grid content-center bg-[var(--lk-bg)]"
      >
        <LiveKitRoom
          token={connectionDetails.participantToken}
          serverUrl={connectionDetails.serverUrl}
          connect={connectionDetails !== undefined}
          audio={true}
          video={false}
          onMediaDeviceFailure={onDeviceFailure}
          onDisconnected={() => {
            updateConnectionDetails(undefined)
          }}
          className="grid grid-rows-[2fr_1fr] items-center"
        >
          <SimpleVoiceAssistant 
            onStateChange={setAgentState} 
            onTranscription={handleTranscription}
          />
          <ControlBar
            onConnectButtonClicked={onConnectButtonClicked}
            onEndSession={handleVoiceSessionEnd}
            agentState={agentState}
          />
          <RoomAudioRenderer />
          <NoAgentNotification state={agentState} />
        </LiveKitRoom>
      </main>
    )
  }

  // Add the text message view after voice session ends
  if (showTextMessages && voiceSessionMessages.length > 0) {
    return (
      <div className="h-full flex flex-col bg-gray-50 p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Voice Session Transcript</h2>
          <Button 
            variant="outline" 
            onClick={() => setShowTextMessages(false)}
          >
            New Session
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto space-y-4 p-2">
          {voiceSessionMessages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className={`text-xs mt-1 ${
                  msg.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col items-center justify-center px-4 bg-gray-50">
      {/* Authentication Warning */}
      {!userAuthenticated && (
        <Alert className="mb-6 max-w-md border-orange-200 bg-orange-50">
          <Shield className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800">
            You need to be logged in to start a voice session. Please log in first.
          </AlertDescription>
        </Alert>
      )}

      {/* Welcome Message */}
      <div className="text-center mb-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">How can I help with your health today?</h2>
        <p className="text-lg text-gray-600 max-w-2xl">
          I'm your AI medical assistant. Start a voice consultation to discuss your symptoms or health concerns.
        </p>
      </div>

      {/* Central orb */}
      <div className="relative mb-16">
        <div
          className={`w-48 h-48 rounded-full bg-gradient-to-br from-blue-200 via-blue-400 to-blue-600 shadow-2xl transition-all duration-300 ${
            isConnecting ? "animate-pulse scale-110" : "scale-100"
          }`}
          style={{
            background: "radial-gradient(circle at 30% 30%, #e0f2fe, #42a5f5, #1565c0)",
            boxShadow: "0 20px 60px rgba(59, 130, 246, 0.3)",
          }}
        >
          {/* Inner glow effect */}
          <div
            className={`absolute inset-4 rounded-full bg-gradient-to-br from-white/30 to-transparent transition-opacity duration-300 ${
              isConnecting ? "opacity-60" : "opacity-40"
            }`}
          />

          {/* Connecting indicator */}
          {isConnecting && <div className="absolute inset-0 rounded-full border-4 border-blue-300 animate-ping" />}
        </div>
      </div>

      {/* Control buttons */}
      <div className="flex items-center gap-8 mb-8">
        {/* Start Session button */}
        <Button
          onClick={onConnectButtonClicked}
          disabled={!userAuthenticated || isConnecting || !!connectionDetails}
          size="lg"
          className="w-16 h-16 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          {isConnecting ? (
            <Loader2 className="h-6 w-6 text-white animate-spin" />
          ) : (
            <Phone className="h-6 w-6 text-white" />
          )}
        </Button>
      </div>

      {/* Status text */}
      <div className="text-center">
        {isConnecting ? (
          <div className="space-y-2">
            <p className="text-lg text-gray-700 font-medium">Connecting to voice session...</p>
            <p className="text-sm text-gray-500">Please wait while we set up your consultation</p>
          </div>
        ) : !userAuthenticated ? (
          <div className="space-y-2">
            <p className="text-lg text-orange-600 font-medium">Please log in first</p>
            <p className="text-sm text-orange-500">You need to be authenticated to start a voice consultation</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-lg text-gray-500">Tap the phone icon to start your voice consultation</p>
            <p className="text-sm text-gray-400">Your conversation is private and secure</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="mt-12 flex flex-wrap justify-center gap-3">
        <Button variant="outline" size="sm" className="rounded-full">
          Check symptoms
        </Button>
        <Button variant="outline" size="sm" className="rounded-full">
          Medication questions
        </Button>
        <Button variant="outline" size="sm" className="rounded-full">
          General health advice
        </Button>
        <Button variant="outline" size="sm" className="rounded-full">
          Emergency guidance
        </Button>
      </div>
    </div>
  )
}

function SimpleVoiceAssistant(props: {
  onStateChange: (state: AgentState) => void;
  onTranscription?: (text: string, role: 'user' | 'assistant') => void;
}) {
  const { state, audioTrack } = useVoiceAssistant();
  
  useEffect(() => {
    props.onStateChange(state);
  }, [props, state]);
  
  // Add transcription listener
  useEffect(() => {
    const handleTranscription = (event: any) => {
      if (event.detail?.text && event.detail?.isFinal) {
        const role = event.detail.isUser ? 'user' : 'assistant';
        props.onTranscription?.(event.detail.text, role);
      }
    };
    
    document.addEventListener('lk-transcription', handleTranscription);
    return () => {
      document.removeEventListener('lk-transcription', handleTranscription);
    };
  }, [props]);
  
  return (
    <div className="h-[300px] max-w-[90vw] mx-auto">
      <BarVisualizer
        state={state}
        barCount={5}
        trackRef={audioTrack}
        className="agent-visualizer"
        options={{ minHeight: 24 }}
      />
    </div>
  );
}

function ControlBar(props: {
  onConnectButtonClicked: () => void;
  onEndSession: () => void;
  agentState: AgentState;
}) {
  return (
    <div className="relative h-[100px]">
      <AnimatePresence>
        {props.agentState !== "disconnected" &&
          props.agentState !== "connecting" && (
            <motion.div
              initial={{ opacity: 0, top: "10px" }}
              animate={{ opacity: 1, top: 0 }}
              exit={{ opacity: 0, top: "-10px" }}
              transition={{ duration: 0.4, ease: [0.09, 1.04, 0.245, 1.055] }}
              className="flex h-8 absolute left-1/2 -translate-x-1/2 justify-center"
            >
              <VoiceAssistantControlBar controls={{ leave: false }} />
              <DisconnectButton onClick={props.onEndSession}>
                <CloseIcon />
              </DisconnectButton>
            </motion.div>
          )}
      </AnimatePresence>
      {props.agentState === "connecting" && (
        <div className="absolute left-1/2 -translate-x-1/2 text-center">
          <p className="text-sm text-gray-600">Connecting to agent...</p>
        </div>
      )}
    </div>
  );
}
