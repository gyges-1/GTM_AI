/**
 * InputBar — message input with send button.
 */
import { KeyboardEvent, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'

interface Props {
  onSend: (message: string) => void
}

export default function InputBar({ onSend }: Props) {
  const [input, setInput] = useState('')
  const isLoading = useChatStore((s) => s.isLoading)
  const isConnected = useChatStore((s) => s.isConnected)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading || !isConnected) return
    onSend(trimmed)
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className="border-t border-gray-800 bg-gray-900 px-4 py-3">
      {!isConnected && (
        <p className="text-xs text-yellow-500 mb-2 text-center">Connecting to server...</p>
      )}
      <div className="flex items-end gap-2 bg-gray-800 rounded-xl px-3 py-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask about pipeline, forecasts, churn risk..."
          disabled={!isConnected || isLoading}
          className="flex-1 bg-transparent resize-none outline-none text-sm text-gray-100 placeholder-gray-500 py-1 max-h-40"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading || !isConnected}
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-brand-600 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-brand-700 transition-colors"
        >
          <Send size={14} />
        </button>
      </div>
      <p className="text-[10px] text-gray-600 mt-1.5 text-center">
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
