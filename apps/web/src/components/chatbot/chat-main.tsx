'use client'
import { useRef, useEffect } from 'react'
import { useChatbotStore } from '@/store/chatbot-store'
import { ChatMessageItem } from './chat-message'
import { AgentActivity } from './agent-activity'

export function ChatMain() {
  const { messages, isLoading, isSessionLoading } = useChatbotStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-5">
      {isSessionLoading ? (
        <SessionLoadingSkeleton />
      ) : (
        <>
          {messages.length === 0 && !isLoading && <WelcomeScreen />}
          {messages.map((msg) => (
            <ChatMessageItem key={msg.id} message={msg} />
          ))}
          {isLoading && <AgentActivity />}
        </>
      )}
      <div ref={bottomRef} />
    </div>
  )
}

function SessionLoadingSkeleton() {
  return (
    <div className="flex flex-col gap-4 animate-pulse px-2 pt-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
          <div className={`rounded-2xl bg-border/40 h-10 ${i % 2 === 0 ? 'w-48' : 'w-64'}`} />
        </div>
      ))}
    </div>
  )
}

const STARTER_PROMPTS = [
  'Summarize key concepts',
  'Find related documents',
  'What are the main themes?',
  'Extract key entities',
]

function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-4 text-center py-16">
      <span className="text-4xl">⬡</span>
      <div>
        <h2 className="text-lg font-semibold text-foreground">AI Knowledge Workspace</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Ask anything about your vault. Powered by RAG + Knowledge Graph.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-2 max-w-sm w-full">
        {STARTER_PROMPTS.map((prompt) => (
          <StarterPromptButton key={prompt} text={prompt} />
        ))}
      </div>
    </div>
  )
}

function StarterPromptButton({ text }: { text: string }) {
  return (
    <button className="text-left text-xs px-3 py-2.5 rounded-lg border border-border/50 bg-card/40 text-muted-foreground hover:text-foreground hover:bg-accent hover:border-border transition-colors">
      {text}
    </button>
  )
}
