"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Mic, X } from "lucide-react"

export default function VoiceChatInterface() {
  const [isRecording, setIsRecording] = useState(false)
  const [isListening, setIsListening] = useState(false)

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

  return (
    <div className="h-full flex flex-col items-center justify-center px-4 bg-gray-50">
      {/* Welcome Message */}
      <div className="text-center mb-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">How can I help with your health today?</h2>
        <p className="text-lg text-gray-600 max-w-2xl">
          I'm your AI medical assistant. Describe your symptoms or health concerns, and I'll provide helpful information
          and guidance.
        </p>
      </div>

      {/* Central orb */}
      <div className="relative mb-16">
        <div
          className={`w-48 h-48 rounded-full bg-gradient-to-br from-blue-200 via-blue-400 to-blue-600 shadow-2xl transition-all duration-300 ${
            isListening ? "animate-pulse scale-110" : "scale-100"
          }`}
          style={{
            background: "radial-gradient(circle at 30% 30%, #e0f2fe, #42a5f5, #1565c0)",
            boxShadow: "0 20px 60px rgba(59, 130, 246, 0.3)",
          }}
        >
          {/* Inner glow effect */}
          <div
            className={`absolute inset-4 rounded-full bg-gradient-to-br from-white/30 to-transparent transition-opacity duration-300 ${
              isListening ? "opacity-60" : "opacity-40"
            }`}
          />

          {/* Listening indicator */}
          {isListening && <div className="absolute inset-0 rounded-full border-4 border-blue-300 animate-ping" />}
        </div>
      </div>

      {/* Control buttons */}
      <div className="flex items-center gap-8 mb-8">
        {/* Microphone button */}
        <Button
          onClick={handleMicClick}
          disabled={isRecording}
          size="lg"
          className={`w-16 h-16 rounded-full transition-all duration-200 ${
            isRecording ? "bg-red-500 hover:bg-red-600" : "bg-gray-600 hover:bg-gray-700"
          }`}
        >
          <Mic className="h-6 w-6 text-white" />
        </Button>

        {/* Stop button */}
        <Button
          onClick={handleStopClick}
          disabled={!isRecording}
          size="lg"
          variant="outline"
          className="w-16 h-16 rounded-full border-2 border-gray-300 hover:border-gray-400 disabled:opacity-50"
        >
          <X className="h-6 w-6 text-gray-600" />
        </Button>
      </div>

      {/* Status text */}
      <div className="text-center">
        {isRecording ? (
          <div className="space-y-2">
            <p className="text-lg text-gray-700 font-medium">Listening...</p>
            <p className="text-sm text-gray-500">Speak clearly about your health concerns</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-lg text-gray-500">Tap the microphone to start your consultation</p>
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
