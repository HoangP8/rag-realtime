"use client"

import { useState, useEffect } from "react"
import LoginForm from "@/components/login-form"
import StartingPage from "./pages/starting-page"
import ChatingPage from "./pages/chating-page"
import { AuthAPI } from "@/lib/auth-api"
import { VoiceSessionAPI } from "@/lib/voice-session-api"
import { toast } from "sonner"

type ViewState = "main" | "conversation"

export default function MedicalChatbot() {
  // Authentication and user state
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [currentUser, setCurrentUser] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Navigation state
  const [viewState, setViewState] = useState<ViewState>("main")
  const [activeConversation, setActiveConversation] = useState<string | null>(null)

  // Check for existing authentication on component mount
  useEffect(() => {
    const checkAuth = () => {
      if (AuthAPI.isAuthenticated()) {
        const user = AuthAPI.getStoredUser()
        if (user) {
          setCurrentUser(user)
          setIsLoggedIn(true)
        }
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [])

  const handleLogin = (user: any) => {
    setCurrentUser(user)
    setIsLoggedIn(true)
  }

  const handleLogout = async () => {
    setIsLoading(true)
    try {
      await AuthAPI.logout()
    } catch (error) {
      console.error("Logout error:", error)
    } finally {
      setIsLoggedIn(false)
      setCurrentUser(null)
      setIsLoading(false)
      setViewState("main")
      setActiveConversation(null)
    }
  }

  // Add a flag to prevent multiple calls
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);

  const handleStartNewConversation = async () => {
    // Add a flag to prevent multiple calls
    if (isCreatingConversation) {
      console.log('Already creating a conversation, ignoring duplicate call');
      return;
    }
    
    setIsCreatingConversation(true);
    console.log('🚀 Starting new conversation...')

    try {
      // Create a new conversation via API
      const conversation = await VoiceSessionAPI.createConversation("Medical Consultation")
      console.log('✅ Created conversation with ID:', conversation.id)

      // Store the conversation ID and navigate to chat
      setActiveConversation(conversation.id)
      setViewState("conversation")

      toast.success('New conversation started!')
    } catch (error) {
      console.error('❌ Failed to create conversation:', error)
      toast.error('Failed to start new conversation. Please try again.')
    } finally {
      // Reset the flag
      setIsCreatingConversation(false);
    }
  }

  const handleReturnToMain = () => {
    setViewState("main")
    setActiveConversation(null)
  }

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Show login form if not logged in
  if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />
  }

  // If in conversation view, show the chat layout
  if (viewState === "conversation") {
    return (
      <ChatingPage
        currentUser={currentUser}
        onLogout={handleLogout}
        onReturn={handleReturnToMain}
        conversationId={activeConversation}
      />
    )
  }

  // Show starting page with conversation history and main frame
  return (
    <StartingPage
      currentUser={currentUser}
      onLogout={handleLogout}
      onStartNewConversation={handleStartNewConversation}
    />
  )
}
