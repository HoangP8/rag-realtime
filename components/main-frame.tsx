"use client"

import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

interface MainFrameProps {
  onStartNewConversation: () => void
}

export default function MainFrame({ onStartNewConversation }: MainFrameProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-gray-50">
      <div className="text-center space-y-4 mb-8">
        <h2 className="text-3xl font-bold text-gray-900">Welcome to Medical AI Assistant</h2>
        <p className="text-lg text-gray-600 max-w-2xl">
          Start a new conversation to discuss your health concerns with our AI medical assistant.
        </p>
      </div>
      
      <Button
        onClick={onStartNewConversation}
        size="lg"
        className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg rounded-2xl flex items-center gap-3 shadow-lg hover:shadow-xl transition-all"
      >
        <Plus className="h-6 w-6" />
        Start New Conversation
      </Button>

      <div className="mt-12 text-center">
        <p className="text-sm text-gray-500">
          Your conversations are private and secure
        </p>
      </div>
    </div>
  )
} 