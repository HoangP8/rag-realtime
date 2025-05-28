"use client"

import { Button } from "@/components/ui/button"
import { LogOut, Stethoscope } from "lucide-react"
import MainFrame from "@/components/main-frame"
import ConversationHistory from "@/components/conversation-history"

interface StartingPageProps {
  currentUser: any
  onLogout: () => void
  onStartNewConversation: () => void | Promise<void>
}

export default function StartingPage({
  currentUser,
  onLogout,
  onStartNewConversation
}: StartingPageProps) {
  return (
    <div className="flex h-screen bg-white">
      {/* Left Sidebar */}
      <div className="w-80 border-r border-gray-200 flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2 mb-4">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Stethoscope className="h-5 w-5 text-white" />
            </div>
            <span className="font-semibold text-gray-900">Medical AI</span>
          </div>
          <Button
            onClick={onStartNewConversation}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white"
          >
            New Consultation
          </Button>
        </div>

        {/* Conversation History */}
        <div className="flex-1 overflow-hidden">
          <ConversationHistory
            onConversationSelect={onStartNewConversation}
            activeConversation={null}
          />
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {currentUser?.email?.[0].toUpperCase() || "U"}
                </span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">{currentUser?.email || "User"}</p>
                <p className="text-xs text-gray-500">Patient</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-16 border-b border-gray-200 flex items-center justify-between px-6">
          <h1 className="text-xl font-semibold text-gray-900">
            Medical AI Assistant
          </h1>
          <Button
            variant="outline"
            size="sm"
            onClick={onLogout}
            className="flex items-center gap-2"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </Button>
        </div>

        {/* Main Content Area */}
        <div className="flex-1">
          <MainFrame onStartNewConversation={onStartNewConversation} />
        </div>
      </div>
    </div>
  )
}