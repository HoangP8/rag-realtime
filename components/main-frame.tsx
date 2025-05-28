"use client"

import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
// Main Frame is the frame in the middle of each page. 
interface MainFrameProps {
  onStartNewConversation: () => void | Promise<void>
}

export default function MainFrame({ onStartNewConversation }: MainFrameProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-white px-4">
      <div className="text-center space-y-4 mb-8">
        <h1 className="text-4xl font-bold text-gray-900">
          Welcome to Medical AI Assistant
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl">
          Start a new conversation to discuss your health concerns with our AI medical assistant.
        </p>
      </div>

      <Button
        onClick={onStartNewConversation}
        className="bg-blue-600 hover:bg-blue-700 text-white h-12 px-6 rounded-full flex items-center gap-2 text-base font-semibold"
      >
        <Plus className="h-5 w-5" />
        Start New Conversation
      </Button>

      <div className="mt-8 text-center">
        <p className="text-sm text-gray-500">
          Your conversations are private and secure
        </p>
      </div>
    </div>
  )
}