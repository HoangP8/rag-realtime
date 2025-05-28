"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  X,
  Settings,
  LogOut,
  Plus,
  Menu,
  MessageSquare,
  Stethoscope,
  ArrowLeft,
} from "lucide-react"
import VoiceChatInterface from "@/components/voice-chat-interface"
import ConversationHistory from "@/components/conversation-history"

interface ChatingPageProps {
  currentUser: any
  onLogout: () => void
  onReturn: () => void
  conversationId?: string | null
}

export default function ChatingPage({
  currentUser,
  onLogout,
  onReturn,
  conversationId
}: ChatingPageProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeConversation, setActiveConversation] = useState<string | null>(conversationId || null)

  const handleNewChat = () => {
    setActiveConversation(null)
  }

  const handleConversationSelect = (id: string) => {
    setActiveConversation(id)
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
          <Button onClick={handleNewChat} className="w-full justify-start bg-blue-600 hover:bg-blue-700 text-white">
            <Plus className="h-4 w-4 mr-2" />
            New Consultation
          </Button>
        </div>

        {/* Conversation History Component */}
        <div className="flex-1 overflow-hidden">
          <ConversationHistory
            onConversationSelect={handleConversationSelect}
            activeConversation={activeConversation}
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
              <Button variant="ghost" size="sm" onClick={onLogout}>
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
                onClick={onReturn}
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
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              <MessageSquare className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Chat Content */}
        <div className="flex-1">
          <VoiceChatInterface conversationId={activeConversation} />
        </div>
      </div>
    </div>
  )
}