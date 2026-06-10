import type { RunLog } from '@/features/runs/store/runsStore'

export type Tab = 'output' | 'input'
export type ViewMode = 'tree' | 'code'

export interface NodeInfo {
  label: string
  icon: string
  color?: string
}

export type LogStatus = 'completed' | 'failed'

export function logStatus(log: RunLog): LogStatus {
  if (log.payload && 'error' in log.payload) return 'failed'
  if (log.level === 'error') return 'failed'
  return 'completed'
}

/** A node-completion log carries either an output or error payload. */
export function isNodeCompletionLog(log: RunLog): boolean {
  return !!log.nodeId && !!log.payload && ('output' in log.payload || 'error' in log.payload)
}
