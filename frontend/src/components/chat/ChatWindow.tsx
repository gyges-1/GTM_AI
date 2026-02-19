/**
 * ChatWindow — top-level chat component managing thread lifecycle.
 */
import { useEffect, useState } from 'react'
import { useChat } from '../../hooks/useChat'
import InputBar from './InputBar'
import MessageList from './MessageList'

function generateThreadId(): string {
  return `thread-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export default function ChatWindow() {
  const [threadId, setThreadId] = useState<string | null>(null)

  useEffect(() => {
    // Create a new thread on mount
    setThreadId(generateThreadId())
  }, [])

  const { sendMessage } = useChat(threadId)

  const handleSend = (text: string) => {
    sendMessage(text)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-900/50">
        <span className="text-xs text-gray-500 font-mono">{threadId ?? '—'}</span>
        <button
          onClick={() => setThreadId(generateThreadId())}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
        >
          New conversation
        </button>
      </div>

      <MessageList />
      <InputBar onSend={handleSend} />
    </div>
  )
}
