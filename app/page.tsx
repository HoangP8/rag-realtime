"use client"

import { useState, useEffect } from "react"
import LoginForm from "@/components/login-form"
import StartingPage from "./pages/starting-page"
import ChatingPage from "./pages/chating-page"
import { AuthAPI } from "@/lib/auth-api"

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

  const handleStartNewConversation = () => {
    setViewState("conversation")
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
