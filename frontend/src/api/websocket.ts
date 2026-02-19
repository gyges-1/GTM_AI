/**
 * GTMWebSocket — manages a WebSocket connection to the streaming chat endpoint.
 */

export type StreamChunkType =
  | 'token'
  | 'agent_switch'
  | 'tool_call'
  | 'tool_result'
  | 'done'
  | 'error'

export interface StreamChunk {
  type: StreamChunkType
  content?: string
  agent_name?: string
  tool_name?: string
  tool_input?: Record<string, unknown>
  tool_output?: string
  error?: string
  thread_id?: string
}

export type ChunkHandler = (chunk: StreamChunk) => void
export type ErrorHandler = (error: Event) => void
export type CloseHandler = () => void

export class GTMWebSocket {
  private ws: WebSocket | null = null
  private threadId: string
  private onChunk: ChunkHandler
  private onError: ErrorHandler
  private onClose: CloseHandler
  private reconnectAttempts = 0
  private readonly maxReconnects = 3

  constructor(
    threadId: string,
    onChunk: ChunkHandler,
    onError: ErrorHandler = () => {},
    onClose: CloseHandler = () => {},
  ) {
    this.threadId = threadId
    this.onChunk = onChunk
    this.onError = onError
    this.onClose = onClose
  }

  connect(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/api/v1/ws/chat/${this.threadId}`

    this.ws = new WebSocket(url)

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const chunk: StreamChunk = JSON.parse(event.data as string)
        this.onChunk(chunk)
      } catch {
        // ignore malformed frames
      }
    }

    this.ws.onerror = (error: Event) => {
      this.onError(error)
    }

    this.ws.onclose = () => {
      this.onClose()
    }
  }

  sendMessage(message: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected')
    }
    this.ws.send(JSON.stringify({ message }))
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
