/**
 * MessageList — renders the conversation history + live streaming message.
 */
import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { useChatStore } from '../../store/chatStore'
import AgentBadge from './AgentBadge'

export default function MessageList() {
  const messages = useChatStore((s) => s.messages)
  const streamingTokens = useChatStore((s) => s.streamingTokens)
  const activeAgent = useChatStore((s) => s.activeAgent)
  const isLoading = useChatStore((s) => s.isLoading)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingTokens])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-center gap-3 text-gray-500 mt-20">
          <div className="text-4xl">📊</div>
          <p className="text-lg font-medium text-gray-400">Ask anything about your GTM</p>
          <p className="text-sm max-w-sm">
            Pipeline coverage, revenue forecast, churn risk, campaign performance — just ask.
          </p>
        </div>
      )}

      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-brand-600 text-white rounded-br-sm'
                : 'bg-gray-800 text-gray-100 rounded-bl-sm'
            }`}
          >
            {msg.role === 'assistant' && msg.agentName && (
              <div className="mb-2">
                <AgentBadge agentName={msg.agentName} size="xs" />
              </div>
            )}
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          </div>
        </div>
      ))}

      {/* Live streaming message */}
      {(isLoading || streamingTokens) && (
        <div className="flex justify-start">
          <div className="max-w-[80%] rounded-2xl rounded-bl-sm px-4 py-3 bg-gray-800 text-gray-100">
            {activeAgent && (
              <div className="mb-2">
                <AgentBadge agentName={activeAgent} size="xs" />
              </div>
            )}
            {streamingTokens ? (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{streamingTokens}</ReactMarkdown>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 h-5">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
              </div>
            )}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
