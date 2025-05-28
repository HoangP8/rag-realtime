"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Search,
  Library,
  Clock,
  MoreHorizontal,
} from "lucide-react"
import { useRouter } from "next/navigation"

interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  metadata?: Record<string, any>
  preview?: string // Added for compatibility with existing code
}

interface ConversationHistoryProps {
  onConversationSelect: (id: string) => void
  activeConversation: string | null
}

export default function ConversationHistory({ onConversationSelect, activeConversation }: ConversationHistoryProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleConversationClick = (conversation: Conversation) => {
    if (onConversationSelect) {
      onConversationSelect(conversation)
    }
    router.push(`/chat/${conversation.id}`)
  }

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setLoading(true)
        // Get token from localStorage
        const access_token = localStorage.getItem("access_token")
        
        if (!access_token) {
          setError("Not authenticated")
          setLoading(false)
          return
        }

        const response = await fetch("https://medbot-backend.fly.dev/api/v1/conversations/", {
          headers: {
            "Authorization": `Bearer ${access_token}`,
            "X-API-Auth": `Bearer ${access_token}` 
          }
        })

        if (!response.ok) {
          console.log("Response Fail")
          throw new Error(`Failed to fetch conversations: ${response.status}`)
        }
        else 
        {
          console.log("Response: OK")
        }

        const data = await response.json()
        
        // Add preview field for compatibility with existing code
        const conversationsWithPreview = data.map((conv: Conversation) => ({
          ...conv,
          preview: conv.metadata?.lastMessage || "No messages yet..."
        }))
        
        setConversations(conversationsWithPreview)
        setError(null)
      } catch (err) {
        console.error("Error fetching conversations:", err)
        setError(err instanceof Error ? err.message : "Failed to load conversations")
      } finally {
        setLoading(false)
      }
    }

    fetchConversations()
  }, [])

  const groupConversationsByTime = (conversations: Conversation[]) => {
    // Set the time milestones based on current time
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
    // Create groups of conversations including today, yesterday, previousWeek and older
    const groups = {
      today: [] as Conversation[],
      yesterday: [] as Conversation[],
      previousWeek: [] as Conversation[],
      older: [] as Conversation[],
    }

    conversations.forEach((conv) => {
      if (new Date(conv.updated_at) >= today) {
        groups.today.push(conv)
      } else if (new Date(conv.updated_at) >= yesterday) {
        groups.yesterday.push(conv)
      } else if (new Date(conv.updated_at) >= weekAgo) {
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

  const formatTime = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
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
            <div
              key={conv.id}
              onClick={() => handleConversationClick(conv)}
              className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors group ${
                activeConversation === conv.id ? "bg-gray-100" : ""
              }`}
            >
              <div className="flex items-start justify-between">
                <div
                  className="flex-1 min-w-0"
                  onClick={() => onConversationSelect(conv.id)}
                >
                  <p className="text-sm font-medium text-gray-900 truncate">{conv.title}</p>
                  <p className="text-xs text-gray-500 truncate mt-1">{conv.preview}</p>
                </div>
                <div className="flex items-center space-x-1 ml-2">
                  <span className="text-xs text-gray-400">{formatTime(conv.updated_at)}</span>
                  <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 h-6 w-6 p-0">
                    <MoreHorizontal className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
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
