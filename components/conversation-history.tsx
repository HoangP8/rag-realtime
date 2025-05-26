"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Search,
  Library,
  Clock,
  MoreHorizontal,
} from "lucide-react"

interface Conversation {
  id: string
  title: string
  timestamp: Date
  preview: string
}

interface ConversationHistoryProps {
  onConversationSelect: (id: string) => void
  activeConversation: string | null
}

export default function ConversationHistory({ onConversationSelect, activeConversation }: ConversationHistoryProps) {
  const [searchQuery, setSearchQuery] = useState("")

  // Mock conversation data - replace with real data from your API
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
              onClick={() => onConversationSelect(conv.id)}
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

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Navigation Items */}
      <div className="p-4 border-b border-gray-200">
        <div className="space-y-2">
          <Button variant="ghost" className="w-full justify-start">
            <Library className="h-4 w-4 mr-2" />
            Medical Library
          </Button>
          <Button variant="ghost" className="w-full justify-start">
            <Clock className="h-4 w-4 mr-2" />
            Appointment History
          </Button>
        </div>
      </div>

      {/* Conversation History */}
      <div className="flex-1 overflow-y-auto p-4">
        <ConversationGroup title="Today" conversations={groupedConversations.today} />
        <ConversationGroup title="Yesterday" conversations={groupedConversations.yesterday} />
        <ConversationGroup title="Previous 7 Days" conversations={groupedConversations.previousWeek} />
        <ConversationGroup title="Older" conversations={groupedConversations.older} />
      </div>
    </div>
  )
} 