import { describe, it, expect, beforeEach } from 'vitest'
import { useChatbotStore } from '@/store/chatbot-store'
import type { ChatMessage } from '@/store/chatbot-store'

function makeMsg(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: 'Hello world',
    timestamp: new Date().toISOString(),
    sources: [],
    timeline: [],
    reasoningExpanded: false,
    ...overrides,
  }
}

const RESET_STATE = {
  sessions: [],
  activeSessionId: undefined,
  messages: [],
  isSessionLoading: false,
  rightPanelTab: 'sources' as const,
  composerMode: 'default' as const,
  isLoading: false,
  error: null,
}

describe('ChatbotStore', () => {
  beforeEach(() => {
    useChatbotStore.setState(RESET_STATE)
  })

  describe('sessions', () => {
    it('sets sessions list', () => {
      const session = { id: 's1', title: 'Test', context: null, created_at: '', updated_at: '' }
      useChatbotStore.getState().setSessions([session])
      expect(useChatbotStore.getState().sessions).toHaveLength(1)
      expect(useChatbotStore.getState().sessions[0].id).toBe('s1')
    })

    it('prepends new session via addSession', () => {
      const s1 = { id: 's1', title: 'First', context: null, created_at: '', updated_at: '' }
      const s2 = { id: 's2', title: 'Second', context: null, created_at: '', updated_at: '' }
      useChatbotStore.getState().setSessions([s1])
      useChatbotStore.getState().addSession(s2)
      expect(useChatbotStore.getState().sessions[0].id).toBe('s2')
    })

    it('setActiveSession sets id, clears messages, and starts session loading', () => {
      useChatbotStore.setState({ messages: [makeMsg()] })
      useChatbotStore.getState().setActiveSession('s1')
      expect(useChatbotStore.getState().activeSessionId).toBe('s1')
      expect(useChatbotStore.getState().messages).toHaveLength(0)
      expect(useChatbotStore.getState().isSessionLoading).toBe(true)
    })

    it('setActiveSession with undefined clears session loading', () => {
      useChatbotStore.setState({ activeSessionId: 's1', isSessionLoading: true })
      useChatbotStore.getState().setActiveSession(undefined)
      expect(useChatbotStore.getState().activeSessionId).toBeUndefined()
      expect(useChatbotStore.getState().isSessionLoading).toBe(false)
    })

    it('removeSession removes it from the list', () => {
      const s1 = { id: 's1', title: 'A', context: null, created_at: '', updated_at: '' }
      const s2 = { id: 's2', title: 'B', context: null, created_at: '', updated_at: '' }
      useChatbotStore.setState({ sessions: [s1, s2] })
      useChatbotStore.getState().removeSession('s1')
      expect(useChatbotStore.getState().sessions).toHaveLength(1)
      expect(useChatbotStore.getState().sessions[0].id).toBe('s2')
    })

    it('removeSession clears messages if active session is deleted', () => {
      const s1 = { id: 's1', title: 'A', context: null, created_at: '', updated_at: '' }
      useChatbotStore.setState({ sessions: [s1], activeSessionId: 's1', messages: [makeMsg()] })
      useChatbotStore.getState().removeSession('s1')
      expect(useChatbotStore.getState().activeSessionId).toBeUndefined()
      expect(useChatbotStore.getState().messages).toHaveLength(0)
    })

    it('removeSession does not clear messages if a different session is deleted', () => {
      const s1 = { id: 's1', title: 'A', context: null, created_at: '', updated_at: '' }
      const s2 = { id: 's2', title: 'B', context: null, created_at: '', updated_at: '' }
      const msg = makeMsg()
      useChatbotStore.setState({ sessions: [s1, s2], activeSessionId: 's2', messages: [msg] })
      useChatbotStore.getState().removeSession('s1')
      expect(useChatbotStore.getState().activeSessionId).toBe('s2')
      expect(useChatbotStore.getState().messages).toHaveLength(1)
    })

    it('unsets active session', () => {
      useChatbotStore.setState({ activeSessionId: 's1' })
      useChatbotStore.getState().setActiveSession(undefined)
      expect(useChatbotStore.getState().activeSessionId).toBeUndefined()
    })
  })

  describe('messages', () => {
    it('adds a message', () => {
      const msg = makeMsg({ role: 'user', content: 'hi' })
      useChatbotStore.getState().addMessage(msg)
      expect(useChatbotStore.getState().messages).toHaveLength(1)
      expect(useChatbotStore.getState().messages[0].content).toBe('hi')
    })

    it('appends messages in order', () => {
      useChatbotStore.getState().addMessage(makeMsg({ id: 'a', content: 'first' }))
      useChatbotStore.getState().addMessage(makeMsg({ id: 'b', content: 'second' }))
      const msgs = useChatbotStore.getState().messages
      expect(msgs[0].id).toBe('a')
      expect(msgs[1].id).toBe('b')
    })

    it('setMessages replaces all messages and clears session loading', () => {
      useChatbotStore.setState({ messages: [makeMsg()], isSessionLoading: true })
      const newMsgs = [makeMsg({ id: 'x', content: 'loaded' })]
      useChatbotStore.getState().setMessages(newMsgs)
      expect(useChatbotStore.getState().messages).toHaveLength(1)
      expect(useChatbotStore.getState().messages[0].id).toBe('x')
      expect(useChatbotStore.getState().isSessionLoading).toBe(false)
    })

    it('clears all messages', () => {
      useChatbotStore.setState({ messages: [makeMsg(), makeMsg()] })
      useChatbotStore.getState().clearMessages()
      expect(useChatbotStore.getState().messages).toHaveLength(0)
    })

    it('toggles reasoning expanded for a specific message', () => {
      const msg = makeMsg({ id: 'msg1', reasoningExpanded: false })
      useChatbotStore.setState({ messages: [msg] })
      useChatbotStore.getState().toggleReasoning('msg1')
      expect(useChatbotStore.getState().messages[0].reasoningExpanded).toBe(true)
      useChatbotStore.getState().toggleReasoning('msg1')
      expect(useChatbotStore.getState().messages[0].reasoningExpanded).toBe(false)
    })

    it('does not affect other messages when toggling reasoning', () => {
      const m1 = makeMsg({ id: 'm1', reasoningExpanded: false })
      const m2 = makeMsg({ id: 'm2', reasoningExpanded: false })
      useChatbotStore.setState({ messages: [m1, m2] })
      useChatbotStore.getState().toggleReasoning('m1')
      expect(useChatbotStore.getState().messages[0].reasoningExpanded).toBe(true)
      expect(useChatbotStore.getState().messages[1].reasoningExpanded).toBe(false)
    })
  })

  describe('UI state', () => {
    it('sets right panel tab', () => {
      useChatbotStore.getState().setRightPanelTab('timeline')
      expect(useChatbotStore.getState().rightPanelTab).toBe('timeline')
    })

    it('sets composer mode', () => {
      useChatbotStore.getState().setComposerMode('deep-research')
      expect(useChatbotStore.getState().composerMode).toBe('deep-research')
    })

    it('sets loading state', () => {
      useChatbotStore.getState().setLoading(true)
      expect(useChatbotStore.getState().isLoading).toBe(true)
      useChatbotStore.getState().setLoading(false)
      expect(useChatbotStore.getState().isLoading).toBe(false)
    })

    it('sets and clears session loading via setSessionLoading', () => {
      useChatbotStore.getState().setSessionLoading(true)
      expect(useChatbotStore.getState().isSessionLoading).toBe(true)
      useChatbotStore.getState().setSessionLoading(false)
      expect(useChatbotStore.getState().isSessionLoading).toBe(false)
    })

    it('sets and clears error', () => {
      useChatbotStore.getState().setError('Network error')
      expect(useChatbotStore.getState().error).toBe('Network error')
      useChatbotStore.getState().setError(null)
      expect(useChatbotStore.getState().error).toBeNull()
    })
  })
})

