/**
 * useChat — manages WebSocket connection and streaming message state.
 */
import { useCallback, useEffect, useRef } from 'react'
import { GTMWebSocket, StreamChunk } from '../api/websocket'
import { useChatStore } from '../store/chatStore'

export function useChat(threadId: string | null) {
  const wsRef = useRef<GTMWebSocket | null>(null)
  const {
    addMessage,
    appendToken,
    finalizeStreamingMessage,
    setActiveAgent,
    setConnected,
    setLoading,
    clearStreamingTokens,
    setActiveThread,
  } = useChatStore()

  // Initialise / switch thread
  useEffect(() => {
    if (!threadId) return

    setActiveThread(threadId)

    // Cleanup old connection
    wsRef.current?.disconnect()

    const handleChunk = (chunk: StreamChunk) => {
      switch (chunk.type) {
        case 'token':
          appendToken(chunk.content ?? '')
          break

        case 'agent_switch':
          setActiveAgent(chunk.agent_name ?? null)
          break

        case 'tool_call':
          // Tool calls are handled visually via the streaming message
          break

        case 'done':
          finalizeStreamingMessage()
          setLoading(false)
          break

        case 'error':
          clearStreamingTokens()
          setLoading(false)
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: `Error: ${chunk.error ?? 'Unknown error'}`,
            createdAt: new Date(),
          })
          break
      }
    }

    const ws = new GTMWebSocket(
      threadId,
      handleChunk,
      () => setConnected(false),
      () => setConnected(false),
    )

    ws.connect()
    wsRef.current = ws

    // Wait for connection
    const checkInterval = setInterval(() => {
      if (ws.isConnected) {
        setConnected(true)
        clearInterval(checkInterval)
      }
    }, 100)

    return () => {
      clearInterval(checkInterval)
      ws.disconnect()
      setConnected(false)
    }
  }, [threadId]) // eslint-disable-line react-hooks/exhaustive-deps

  const sendMessage = useCallback(
    (text: string) => {
      if (!wsRef.current?.isConnected) return false

      addMessage({
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        createdAt: new Date(),
      })

      clearStreamingTokens()
      setLoading(true)
      wsRef.current.sendMessage(text)
      return true
    },
    [addMessage, clearStreamingTokens, setLoading],
  )

  return { sendMessage }
}
