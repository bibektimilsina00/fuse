import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { requestJson } from '@/lib/api/client'
import { ExecutionSchema, type Execution } from '@/lib/api/contracts'
import { z } from 'zod'
import { useCallback, useEffect } from 'react'
import { useExecutionStream } from '@/features/workflow-editor/hooks/use-execution-stream'
import { useExecutionStore } from '@/stores/execution-store'
import { useWorkflowStore } from '@/stores/workflow-store'

const RunResponseSchema = z.object({
  execution_id: z.string().uuid(),
})

export const executionKeys = {
  all: ['executions'] as const,
  details: () => [...executionKeys.all, 'detail'] as const,
  detail: (id: string) => [...executionKeys.details(), id] as const,
}

export function useExecution() {
  const { id: workflowId } = useParams<{ id: string }>()
  const {
    currentExecutionId,
    setCurrentExecutionId,
    setExecutionPanelOpen,
    addRun,
    updateRun,
  } = useExecutionStore()
  const { nodes, edges } = useWorkflowStore()
  const queryClient = useQueryClient()

  // WebSocket Streaming
  const { isRunning: isStreaming } = useExecutionStream(currentExecutionId)

  const runMutation = useMutation({
    mutationFn: async () => {
      if (!workflowId) throw new Error('Workflow ID is required')
      // Send current in-memory graph so execution is never blocked by auto-save debounce
      return requestJson(RunResponseSchema, {
        url: `/workflows/${workflowId}/run`,
        method: 'POST',
        data: { nodes, edges },
      })
    },
    onSuccess: (data) => {
      setCurrentExecutionId(data.execution_id)
      setExecutionPanelOpen(true)
      addRun(data.execution_id)
      queryClient.invalidateQueries({ queryKey: executionKeys.all })
    },
  })

  const executionQuery = useQuery({
    queryKey: executionKeys.detail(currentExecutionId || ''),
    queryFn: async ({ signal }) => {
      if (!currentExecutionId) throw new Error('Execution ID is required')
      return requestJson(ExecutionSchema, {
        url: `/executions/${currentExecutionId}`,
        method: 'GET',
        signal,
      })
    },
    enabled: !!currentExecutionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') return false
      return 1000
    },
  })

  // Sync polling data into run history (fallback and initial load)
  useEffect(() => {
    if (executionQuery.data && currentExecutionId) {
      updateRun(currentExecutionId, executionQuery.data.logs, executionQuery.data.status)
    }
  }, [executionQuery.data, currentExecutionId, updateRun])

  const run = useCallback(() => {
    runMutation.mutate()
  }, [runMutation])

  const status = executionQuery.data?.status
  const isRunning = runMutation.isPending || isStreaming || status === 'running' || status === 'pending'

  return {
    run,
    isRunning,
    execution: executionQuery.data as Execution | undefined,
    error: runMutation.error || executionQuery.error,
    currentExecutionId,
  }
}
