"use client"

import { useState, useEffect, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, Send, Mic, MicOff, Menu, X, Stethoscope, LogOut, Settings, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import ConversationHistory from "@/components/conversation-history"
import VoiceChatInterface from "@/components/voice-chat-interface"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  created_at: string
  message_type: string
  voice_url?: string | null
}

export default function ChatPage() {
  const { id } = useParams()
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isVoiceMode, setIsVoiceMode] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentUser, setCurrentUser] = useState<any>({})

  useEffect(() => {
    // Get user info from localStorage
    const userEmail = localStorage.getItem("user_email") || "User"
    setCurrentUser({ email: userEmail })
  }, [])

  // Fetch messages for the conversation
  useEffect(() => {
    const fetchMessages = async () => {
      setIsFetching(true)
      try {
        const authToken = localStorage.getItem("access_token")
        if (!authToken) {
          console.error("No auth token found")
          return
        }

        const response = await fetch(`https://medbot-backend.fly.dev/api/v1/conversations/${id}/messages`, {
          headers: {
            "Authorization": `Bearer ${authToken}`,
            "X-API-Auth": `Bearer ${authToken}`
          }
        })

        if (!response.ok) {
          throw new Error("Failed to fetch messages")
        }

        const data = await response.json()
        setMessages(data)
      } catch (error) {
        console.error("Error fetching messages:", error)
      } finally {
        setIsFetching(false)
      }
    }

    if (id) {
      fetchMessages()
    }
  }, [id])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const newMessage: Partial<Message> = {
      role: "user",
      content: inputValue,
      message_type: "text"
    }

    setMessages(prev => [...prev, newMessage as Message])
    setInputValue("")
    setIsLoading(true)

    try {
      const authToken = localStorage.getItem("access_token")
      if (!authToken) {
        console.error("No auth token found")
        return
      }

      const response = await fetch(`https://medbot-backend.fly.dev/api/v1/conversations/${id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`,
          "X-API-Auth": `Bearer ${authToken}`
        },
        body: JSON.stringify(newMessage)
      })

      if (!response.ok) {
        throw new Error("Failed to send message")
      }

      // Fetch updated messages to get the AI response
      const messagesResponse = await fetch(`https://medbot-backend.fly.dev/api/v1/conversations/${id}/messages`, {
        headers: {
          "Authorization": `Bearer ${authToken}`,
          "X-API-Auth": `Bearer ${authToken}`
        }
      })

      if (messagesResponse.ok) {
        const data = await messagesResponse.json()
        setMessages(data)
      }
    } catch (error) {
      console.error("Error sending message:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const toggleVoiceMode = () => {
    setIsVoiceMode(!isVoiceMode)
  }

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    router.push("/login")
  }

  const handleConversationSelect = (selectedId: string) => {
    router.push(`/chat/${selectedId}`)
  }

  const handleReturnToMain = () => {
    router.push("/")
  }

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <div
        className={`${sidebarOpen ? "w-80" : "w-0"} transition-all duration-300 overflow-hidden border-r border-gray-200 flex flex-col`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Stethoscope className="h-5 w-5 text-white" />
              </div>
              <span className="font-semibold text-gray-900">Medical AI</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(false)} className="lg:hidden">
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* New Chat Button */}
          <Button onClick={() => router.push("/")} className="w-full justify-start bg-blue-600 hover:bg-blue-700 text-white">
            <span className="mr-2">+</span>
            New Consultation
          </Button>
        </div>

        {/* Conversation History Component */}
        <div className="flex-1 overflow-hidden">
          <ConversationHistory
            onConversationSelect={handleConversationSelect}
            activeConversation={id as string}
          />
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {currentUser?.email?.charAt(0).toUpperCase() || "U"}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{currentUser?.email || "User"}</p>
                <p className="text-xs text-gray-500">Patient</p>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-16 border-b border-gray-200 flex items-center justify-between px-4">
          <div className="flex items-center space-x-4">
            {!sidebarOpen && (
              <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(true)}>
                <Menu className="h-5 w-5" />
              </Button>
            )}
            <div className="flex items-center space-x-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleReturnToMain}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Return</span>
              </Button>
              <h1 className="text-lg font-semibold text-gray-900">
                Medical Consultation
              </h1>
            </div>
          </div>
          <div className="flex items-center">
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

        {/* Chat Content */}
        <div className="flex-1 flex flex-col">
          {isVoiceMode ? (
            <VoiceChatInterface />
          ) : (
            <>
              {/* Chat messages with ScrollArea */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-6">
                  {isFetching ? (
                    <div className="flex justify-center items-center h-full py-20">
                      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="flex justify-center items-center h-full py-20 text-gray-500">
                      No messages yet. Start a conversation!
                    </div>
                  ) : (
                    messages.map((message, index) => (
                      <div 
                        key={message.id || index} 
                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div 
                          className={`max-w-[80%] rounded-lg p-4 ${
                            message.role === "user" 
                              ? "bg-blue-500 text-white" 
                              : "bg-gray-100 text-gray-900"
                          }`}
                        >
                          <div className="whitespace-pre-wrap">{message.content}</div>
                          <div className={`text-xs mt-1 ${message.role === "user" ? "text-blue-100" : "text-gray-500"}`}>
                            {message.created_at && formatTime(message.created_at)}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg p-4 max-w-[80%]">
                        <div className="flex items-center space-x-2">
                          <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                          <span className="text-gray-500">AI is thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Input area */}
              <div className="border-t p-4">
                <div className="flex items-end space-x-2">
                  <Textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 min-h-[60px] max-h-[200px]"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        handleSendMessage()
                      }
                    }}
                    disabled={isLoading}
                  />
                  <div className="flex flex-col space-y-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={toggleVoiceMode}
                      className="h-16 w-16 rounded-full"
                    >
                      <Mic className="h-8 w-8 text-blue-500" />
                    </Button>
                    <Button
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || isLoading}
                      className="h-10"
                    >
                      <Send className="h-5 w-5" />
                    </Button>
                  </div>
                </div>
                <div className="text-xs text-center text-gray-500 mt-2">
                  Medical AI can make mistakes. Check important info.
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
