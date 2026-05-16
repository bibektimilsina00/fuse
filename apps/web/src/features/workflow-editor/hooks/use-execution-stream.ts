import { useEffect, useState } from 'react'
import { connectExecutionWebSocket, type ExecutionEvent } from '@/lib/websocket/client'
import { useAuthStore } from '@/stores/auth-store'
import { useExecutionStore } from '@/stores/execution-store'

export function useExecutionStream(executionId: string | null) {
  const token = useAuthStore((s) => s.token)
  const { addLog, updateRunStatus } = useExecutionStore()
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    if (!executionId || !token) return

    setIsRunning(true)
    updateRunStatus(executionId, 'running')

    const ws = connectExecutionWebSocket(
      executionId,
      token,
      {
        onEvent: (event: ExecutionEvent) => {
          // Handle status updates
          if (event.type === 'execution_completed') {
            setIsRunning(false)
            updateRunStatus(executionId, 'completed')
          } else if (event.type === 'execution_failed') {
            setIsRunning(false)
            updateRunStatus(executionId, 'failed')
          }

          // Map events to logs
          // For log_synced, we use the provided data directly
          if (event.type === 'log_synced') {
            addLog(executionId, {
              id: event.id ?? `${executionId}:${event.timestamp}:${event.node_id ?? 'workflow'}:${event.message ?? ''}`,
              node_id: event.node_id ?? '',
              level: event.level === 'error' || event.level === 'warn' ? event.level : 'info',
              message: event.message || '',
              timestamp: event.timestamp,
              payload: event.payload || event.output
            })
            return
          }

          const logId = crypto.randomUUID()
          const timestamp = event.timestamp || new Date().toISOString()

          if (event.type === 'node_started') {
            addLog(executionId, {
              id: logId,
              node_id: event.node_id,
              level: 'info',
              message: `Node ${event.label} started`,
              timestamp,
              payload: { node_type: event.node_type }
            })
          } else if (event.type === 'node_completed') {
            addLog(executionId, {
              id: logId,
              node_id: event.node_id,
              level: 'info',
              message: `Node ${event.node_id} completed successfully`,
              timestamp,
              payload: event.output
            })
          } else if (event.type === 'node_failed') {
            addLog(executionId, {
              id: logId,
              node_id: event.node_id,
              level: 'error',
              message: `Node ${event.node_id} failed: ${event.error}`,
              timestamp,
              payload: { error: event.error }
            })
          }
        },
        onClose: () => setIsRunning(false),
      }
    )

    return () => {
      ws.close()
    }
  }, [executionId, token, addLog, updateRunStatus])

  return { isRunning }
}
