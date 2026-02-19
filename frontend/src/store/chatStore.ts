/**
 * Zustand store for chat sessions and streaming state.
 */
import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentName?: string
  toolCalls?: ToolCall[]
  createdAt: Date
  isStreaming?: boolean
}

export interface ToolCall {
  toolName: string
  input?: Record<string, unknown>
  output?: string
}

export interface Session {
  threadId: string
  title?: string
  createdAt: Date
  updatedAt: Date
  messageCount: number
}

interface ChatStore {
  // Sessions
  sessions: Session[]
  activeThreadId: string | null

  // Messages for the active thread
  messages: Message[]
  streamingTokens: string

  // Connection state
  isConnected: boolean
  isLoading: boolean
  activeAgent: string | null

  // Actions
  setActiveThread: (threadId: string) => void
  addMessage: (message: Message) => void
  appendToken: (token: string) => void
  finalizeStreamingMessage: () => void
  setActiveAgent: (agent: string | null) => void
  setConnected: (connected: boolean) => void
  setLoading: (loading: boolean) => void
  clearStreamingTokens: () => void
  setSessions: (sessions: Session[]) => void
  addSession: (session: Session) => void
}

export const useChatStore = create<ChatStore>((set, get) => ({
  sessions: [],
  activeThreadId: null,
  messages: [],
  streamingTokens: '',
  isConnected: false,
  isLoading: false,
  activeAgent: null,

  setActiveThread: (threadId) => set({ activeThreadId: threadId, messages: [], streamingTokens: '' }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  appendToken: (token) =>
    set((state) => ({ streamingTokens: state.streamingTokens + token })),

  finalizeStreamingMessage: () => {
    const { streamingTokens, activeAgent, messages } = get()
    if (!streamingTokens) return

    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: streamingTokens,
      agentName: activeAgent ?? undefined,
      createdAt: new Date(),
    }
    set((state) => ({
      messages: [...state.messages, assistantMsg],
      streamingTokens: '',
      activeAgent: null,
      isLoading: false,
    }))
  },

  setActiveAgent: (agent) => set({ activeAgent: agent }),
  setConnected: (connected) => set({ isConnected: connected }),
  setLoading: (loading) => set({ isLoading: loading }),
  clearStreamingTokens: () => set({ streamingTokens: '' }),

  setSessions: (sessions) => set({ sessions }),
  addSession: (session) =>
    set((state) => ({ sessions: [session, ...state.sessions] })),
}))
