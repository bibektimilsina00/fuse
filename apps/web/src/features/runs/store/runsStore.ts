import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface RunLog {
  id: string
  nodeId: string | null
  level: 'info' | 'warn' | 'error'
  message: string
  payload: Record<string, unknown> | null
  timestamp: string
}

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface Run {
  executionId: string
  status: RunStatus
  logs: RunLog[]
}

export interface WorkflowRunsSlice {
  runs: Run[]
  activeExecutionId: string | null
  selectedLogId: string | null
}

interface RunsState {
  byWorkflow: Record<string, WorkflowRunsSlice>
  setActiveExecutionId: (workflowId: string, executionId: string | null) => void
  startRun: (workflowId: string, executionId: string) => void
  appendLog: (workflowId: string, executionId: string, log: RunLog) => void
  setStatus: (workflowId: string, executionId: string, status: RunStatus) => void
  setSelectedLogId: (workflowId: string, id: string | null) => void
  clearRuns: (workflowId: string) => void
}

export const EMPTY_SLICE: WorkflowRunsSlice = Object.freeze({
  runs: [],
  activeExecutionId: null,
  selectedLogId: null,
})

const LEVEL_MAP: Record<string, RunLog['level']> = {
  info: 'info',
  warning: 'warn',
  warn: 'warn',
  error: 'error',
  err: 'error',
}

export function normalizeLevel(raw: unknown): RunLog['level'] {
  return LEVEL_MAP[String(raw)] ?? 'info'
}

function readSlice(
  byWorkflow: Record<string, WorkflowRunsSlice>,
  workflowId: string,
): WorkflowRunsSlice {
  return byWorkflow[workflowId] ?? { runs: [], activeExecutionId: null, selectedLogId: null }
}

function withSlice(
  state: { byWorkflow: Record<string, WorkflowRunsSlice> },
  workflowId: string,
  updater: (slice: WorkflowRunsSlice) => WorkflowRunsSlice,
): { byWorkflow: Record<string, WorkflowRunsSlice> } | object {
  const current = readSlice(state.byWorkflow, workflowId)
  const next = updater(current)
  if (next === current) return {}
  return { byWorkflow: { ...state.byWorkflow, [workflowId]: next } }
}

const MAX_RUNS_PER_WORKFLOW = 20

export const useRunsStore = create<RunsState>()(
  persist(
    (set) => ({
  byWorkflow: {},

  setActiveExecutionId: (workflowId, activeExecutionId) =>
    set((s) => withSlice(s, workflowId, (slice) => ({ ...slice, activeExecutionId }))),

  startRun: (workflowId, executionId) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => {
        if (slice.runs.some((r) => r.executionId === executionId)) return slice
        return {
          ...slice,
          runs: [...slice.runs, { executionId, status: 'running', logs: [] }],
        }
      }),
    ),

  appendLog: (workflowId, executionId, log) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => {
        const runs = slice.runs.map((r) => {
          if (r.executionId !== executionId) return r
          if (r.logs.some((l) => l.id === log.id)) return r
          // Content fallback — guards against catch-up replays sending the
          // same log under a different id (synthetic `live-*` vs DB UUID).
          // Timestamp is intentionally excluded: live and catch-up paths can
          // serialize the same instant slightly differently.
          const payloadKey = log.payload ? Object.keys(log.payload).sort().join(',') : ''
          const key = `${log.nodeId ?? ''}|${log.level}|${log.message}|${payloadKey}`
          if (
            r.logs.some(
              (l) =>
                `${l.nodeId ?? ''}|${l.level}|${l.message}|${l.payload ? Object.keys(l.payload).sort().join(',') : ''}` ===
                key,
            )
          ) {
            return r
          }
          return { ...r, logs: [...r.logs, log] }
        })
        // Auto-select the first node log so the inspector isn't empty.
        const selectedLogId = slice.selectedLogId ?? (log.nodeId ? log.id : null)
        return { ...slice, runs, selectedLogId }
      }),
    ),

  setStatus: (workflowId, executionId, status) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => ({
        ...slice,
        runs: slice.runs.map((r) => (r.executionId === executionId ? { ...r, status } : r)),
      })),
    ),

  setSelectedLogId: (workflowId, selectedLogId) =>
    set((s) => withSlice(s, workflowId, (slice) => ({ ...slice, selectedLogId }))),

  clearRuns: (workflowId) =>
    set((s) =>
      withSlice(s, workflowId, () => ({
        runs: [],
        activeExecutionId: null,
        selectedLogId: null,
      })),
    ),
}),
    {
      name: 'fuse-runs',
      version: 2,
      partialize: (s) => ({ byWorkflow: s.byWorkflow }),
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<RunsState>
        const trimmed: Record<string, WorkflowRunsSlice> = {}
        for (const [wfId, slice] of Object.entries(p.byWorkflow ?? {})) {
          // Cap log history to the last MAX_RUNS_PER_WORKFLOW runs to keep
          // localStorage from growing unbounded across long-lived sessions.
          const runs = slice.runs.slice(-MAX_RUNS_PER_WORKFLOW)
          trimmed[wfId] = { ...slice, runs }
        }
        return { ...current, ...p, byWorkflow: trimmed }
      },
    },
  ),
)

/**
 * Read a workflow's runs slice. Returns the frozen empty slice when the
 * workflow has no recorded runs yet — same reference on every miss, so the
 * selector does not trigger re-renders.
 */
export function useWorkflowRuns(workflowId: string | null): WorkflowRunsSlice {
  return useRunsStore((s) => (workflowId ? s.byWorkflow[workflowId] ?? EMPTY_SLICE : EMPTY_SLICE))
}

/**
 * Latest run for a workflow — used by node border styling.
 */
export function useLatestRunForWorkflow(workflowId: string | null): Run | null {
  return useRunsStore((s) => {
    if (!workflowId) return null
    const slice = s.byWorkflow[workflowId]
    if (!slice || !slice.runs.length) return null
    return slice.runs[slice.runs.length - 1]
  })
}
