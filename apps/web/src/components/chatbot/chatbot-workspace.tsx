'use client'
import { useEffect } from 'react'
import { useChatbotStore } from '@/store/chatbot-store'
import { listSessions } from '@/lib/api'
import { ChatSidebar } from './chat-sidebar'
import { ChatMain } from './chat-main'
import { IntelligencePanel } from './intelligence-panel'
import { ChatComposer } from './chat-composer'

export function ChatbotWorkspace() {
  const { setSessions, error } = useChatbotStore()

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setSessions([]))
  }, [setSessions])

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left sidebar: sessions */}
      <ChatSidebar />

      {/* Main workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Error banner */}
        {error && (
          <div className="px-4 py-2 text-xs text-destructive bg-destructive/10 border-b border-destructive/20 flex items-center justify-between">
            <span>{error}</span>
          </div>
        )}

        <ChatMain />
        <ChatComposer />
      </div>

      {/* Right: Intelligence panel */}
      <IntelligencePanel />
    </div>
  )
}
