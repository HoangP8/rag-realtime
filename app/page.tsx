"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  X,
  Settings,
  LogOut,
  Plus,
  Search,
  Library,
  Menu,
  MessageSquare,
  Stethoscope,
  Clock,
  MoreHorizontal,
  Mic,
} from "lucide-react"
import LoginForm from "@/components/login-form"
import ChatLayout from "@/components/chat-layout"
import VoiceChatInterface from "@/components/voice-chat-interface"
import MainFrame from "@/components/main-frame"
import { AuthAPI } from "@/lib/auth-api"

interface Conversation {
  id: string
  title: string
  timestamp: Date
  preview: string
}

// ViewState defines the possible views in the app:
// - "main": Shows the main welcome screen
// - "conversation": Shows an active chat conversation
type ViewState = "main" | "conversation"

export default function MedicalChatbot() {
  // Authentication and user state
  const [isLoggedIn, setIsLoggedIn] = useState(false) // Tracks if user is logged in
  const [currentUser, setCurrentUser] = useState<any>(null) // Stores current user data
  const [isLoading, setIsLoading] = useState(true) // Loading state for initial auth check
  
  // Navigation state
  const [viewState, setViewState] = useState<ViewState>("main") // Controls which view is shown
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null) // ID of active conversation

  // Voice chat feature states
  const [isRecording, setIsRecording] = useState(false) // If voice recording is active
  const [isListening, setIsListening] = useState(false) // If listening for voice input

  // UI state for chat interface
  const [sidebarOpen, setSidebarOpen] = useState(true) // Controls sidebar visibility
  const [searchQuery, setSearchQuery] = useState("") // Stores conversation search text
  const [activeConversation, setActiveConversation] = useState<string | null>(null) // Currently selected conversation

  // Mock conversation data will be defined next...
  const conversations: Conversation[] = [
    {
      id: "1",
      title: "Chest Pain Consultation",
      timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
      preview: "Discussed symptoms of chest discomfort...",
    },
    {
      id: "2",
      title: "Blood Pressure Check",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
      preview: "Reviewed blood pressure readings...",
    },
    {
      id: "3",
      title: "Medication Review",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // Yesterday
      preview: "Discussed current medications and side effects...",
    },
    {
      id: "4",
      title: "Follow-up Appointment",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), // 2 days ago
      preview: "Scheduled follow-up for test results...",
    },
    {
      id: "5",
      title: "Allergy Symptoms",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7), // 1 week ago
      preview: "Discussed seasonal allergy management...",
    },
  ]

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
      setIsRecording(false)
      setIsListening(false)
      setIsLoading(false)
      setViewState("main")
      setCurrentConversationId(null)
    }
  }

  // Voice interface functions
  const handleMicClick = () => {
    if (!isRecording) {
      setIsRecording(true)
      setIsListening(true)
      console.log("Starting voice recording...")
    }
  }

  const handleStopClick = () => {
    setIsRecording(false)
    setIsListening(false)
    console.log("Stopping voice recording...")
  }

  // Chat layout functions
  const groupConversationsByTime = (conversations: Conversation[]) => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)

    const groups = {
      today: [] as Conversation[],
      yesterday: [] as Conversation[],
      previousWeek: [] as Conversation[],
      older: [] as Conversation[],
    }

    conversations.forEach((conv) => {
      if (conv.timestamp >= today) {
        groups.today.push(conv)
      } else if (conv.timestamp >= yesterday) {
        groups.yesterday.push(conv)
      } else if (conv.timestamp >= weekAgo) {
        groups.previousWeek.push(conv)
      } else {
        groups.older.push(conv)
      }
    })

    return groups
  }

  const filteredConversations = conversations.filter(
    (conv) =>
      conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.preview.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const groupedConversations = groupConversationsByTime(filteredConversations)

  const handleNewChat = () => {
    setActiveConversation(null)
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  const ConversationGroup = ({ title, conversations }: { title: string; conversations: Conversation[] }) => {
    if (conversations.length === 0) return null

    return (
      <div className="mb-4">
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 px-3">{title}</h3>
        <div className="space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setActiveConversation(conv.id)}
              className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors group ${
                activeConversation === conv.id ? "bg-gray-100" : ""
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{conv.title}</p>
                  <p className="text-xs text-gray-500 truncate mt-1">{conv.preview}</p>
                </div>
                <div className="flex items-center space-x-1 ml-2">
                  <span className="text-xs text-gray-400">{formatTime(conv.timestamp)}</span>
                  <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 h-6 w-6 p-0">
                    <MoreHorizontal className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    )
  }

  const handleStartNewConversation = async () => {
    try {
      // Here you would typically call your API to create a new conversation
      // For now, we'll just simulate it
      const newConversationId = "conv_" + Date.now()
      setCurrentConversationId(newConversationId)
      setViewState("conversation")
    } catch (error) {
      console.error("Error creating conversation:", error)
    }
  }

  const handleEndConversation = () => {
    setViewState("main")
    setCurrentConversationId(null)
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

  // Show main chat interface if logged in
  return (
    <div className="flex h-screen bg-white">
      {/* Left sidebar with conversation history */}
      <ChatLayout currentUser={currentUser} onLogout={handleLogout} />

      {/* Main content area */}
      <div className="flex-1 flex flex-col">
        {/* Top bar with title and logout */}
        <div className="h-16 border-b border-gray-200 flex items-center justify-between px-6">
          <h1 className="text-xl font-semibold text-gray-900">
            {viewState === "conversation" ? "Medication Review" : "Medical AI Assistant"}
          </h1>
          <div className="flex items-center gap-4">
            {viewState === "conversation" && (
              <Button
                variant="outline"
                onClick={handleEndConversation}
                className="text-gray-600 hover:text-gray-900"
              >
                End Conversation
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="flex items-center gap-2"
            >
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </Button>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1">
          {viewState === "main" ? (
            <MainFrame onStartNewConversation={handleStartNewConversation} />
          ) : (
            <VoiceChatInterface />
          )}
        </div>
      </div>
    </div>
  )
}
