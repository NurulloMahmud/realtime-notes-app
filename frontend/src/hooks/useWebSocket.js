import { useEffect, useRef, useCallback } from 'react'

const AUTH_FAILURE_CODES = [4001, 4003, 4004]

export function useWebSocket(noteId, onMessage) {
  const wsRef = useRef(null)
  const reconnectRef = useRef(null)
  const onMessageRef = useRef(onMessage)

  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token')
    if (!token || !noteId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/notes/${noteId}?token=${token}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessageRef.current(data)
      } catch {}
    }

    ws.onclose = (event) => {
      if (AUTH_FAILURE_CODES.includes(event.code)) {
        return
      }
      if (event.code !== 1000) {
        reconnectRef.current = setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [noteId])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectRef.current)
      wsRef.current?.close(1000)
    }
  }, [connect])

  const sendEdit = useCallback((content, cursorPosition) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: 'edit', content, cursor_position: cursorPosition })
      )
    }
  }, [])

  const sendCursor = useCallback((cursorPosition) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: 'cursor', cursor_position: cursorPosition })
      )
    }
  }, [])

  const isConnected = () => wsRef.current?.readyState === WebSocket.OPEN

  return { sendEdit, sendCursor, isConnected }
}
