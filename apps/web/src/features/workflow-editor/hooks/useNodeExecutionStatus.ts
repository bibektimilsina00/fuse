import { useRunsStore } from '@/features/runs/store/runsStore'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'

export type ExecutionStatus = 'running' | 'completed' | 'failed' | null

/**
 * Derives a node's execution status from the current workflow's latest run.
 *  - `failed`    — terminal log carries `payload.error`
 *  - `completed` — terminal log carries `payload.output`
 *  - `running`   — run is in flight and the node has produced at least one log
 *                  without a terminal payload yet
 *  - `null`      — no run, or the node has not been touched
 */
export function useNodeExecutionStatus(nodeId: string): ExecutionStatus {
  const workflowId = useWorkflowEditorStore((s) => s.workflow?.id ?? null)
  return useRunsStore((s) => {
    if (!workflowId) return null
    const slice = s.byWorkflow[workflowId]
    if (!slice) return null
    const latest = slice.runs[slice.runs.length - 1]
    if (!latest) return null

    let touched = false
    for (const log of latest.logs) {
      if (log.nodeId !== nodeId) continue
      touched = true
      if (log.payload && 'error' in log.payload) return 'failed'
      if (log.payload && 'output' in log.payload) return 'completed'
    }

    if (latest.status === 'failed' && touched) return 'failed'
    if (latest.status === 'running' && touched) return 'running'
    return null
  })
}
