import { create } from 'zustand'
import type { MemorySession } from '@/lib/types'

export type RightPanelTab = 'sources' | 'timeline' | 'memory'
export type ComposerMode = 'default' | 'deep-research' | 'use-graph' | 'web-search'

export interface ChatSource {
  resource_id: string
  title: string
  excerpt: string
}

export interface TimelineStep {
  label: string
  ts: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources: ChatSource[]
  turnId?: string
  sessionId?: string
  timeline: TimelineStep[]
  confidence?: number
  reasoningExpanded: boolean
}

interface ChatbotStore {
  sessions: MemorySession[]
  activeSessionId: string | undefined
  messages: ChatMessage[]
  isSessionLoading: boolean
  rightPanelTab: RightPanelTab
  composerMode: ComposerMode
  isLoading: boolean
  error: string | null

  setSessions: (sessions: MemorySession[]) => void
  addSession: (session: MemorySession) => void
  removeSession: (id: string) => void
  setActiveSession: (id: string | undefined) => void
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (msg: ChatMessage) => void
  clearMessages: () => void
  toggleReasoning: (id: string) => void
  setRightPanelTab: (tab: RightPanelTab) => void
  setComposerMode: (mode: ComposerMode) => void
  setLoading: (loading: boolean) => void
  setSessionLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useChatbotStore = create<ChatbotStore>((set) => ({
  sessions: [],
  activeSessionId: undefined,
  messages: [],
  isSessionLoading: false,
  rightPanelTab: 'sources',
  composerMode: 'default',
  isLoading: false,
  error: null,

  setSessions: (sessions) => set({ sessions }),
  addSession: (session) =>
    set((s) => ({ sessions: [session, ...s.sessions] })),
  removeSession: (id) =>
    set((s) => ({
      sessions: s.sessions.filter((sess) => sess.id !== id),
      activeSessionId: s.activeSessionId === id ? undefined : s.activeSessionId,
      messages: s.activeSessionId === id ? [] : s.messages,
    })),
  setActiveSession: (id) => set({ activeSessionId: id, messages: [], error: null, isSessionLoading: id !== undefined }),
  setMessages: (messages) => set({ messages, isSessionLoading: false }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
  toggleReasoning: (id) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, reasoningExpanded: !m.reasoningExpanded } : m
      ),
    })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab }),
  setComposerMode: (mode) => set({ composerMode: mode }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSessionLoading: (loading) => set({ isSessionLoading: loading }),
  setError: (error) => set({ error }),
}))
