import { create } from 'zustand'
import type { ExecutionLog } from '@/lib/api/contracts'

export interface ExecutionRun {
  id: string
  status: string
  logs: ExecutionLog[]
  timestamp: string
}

interface ExecutionState {
  currentExecutionId: string | null
  setCurrentExecutionId: (id: string | null) => void
  isExecutionPanelOpen: boolean
  setExecutionPanelOpen: (open: boolean) => void
  selectedLogId: string | null
  setSelectedLogId: (id: string | null) => void
  runs: ExecutionRun[]
  addRun: (id: string) => void
  updateRun: (id: string, logs: ExecutionLog[], status: string) => void
  addLog: (id: string, log: ExecutionLog) => void
  updateRunStatus: (id: string, status: string) => void
  clearRuns: () => void
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  currentExecutionId: null,
  setCurrentExecutionId: (id) => set({ currentExecutionId: id }),
  isExecutionPanelOpen: false,
  setExecutionPanelOpen: (open) => set({ isExecutionPanelOpen: open }),
  selectedLogId: null,
  setSelectedLogId: (id) => set({ selectedLogId: id }),
  runs: [],
  addRun: (id) =>
    set((state) => ({
      runs: [
        ...state.runs,
        { id, status: 'pending', logs: [], timestamp: new Date().toISOString() },
      ],
    })),
  updateRun: (id, logs, status) =>
    set((state) => ({
      runs: state.runs.map((r) => {
        if (r.id !== id) return r
        // Merge logs, keeping existing ones and adding new ones, avoiding duplicates by ID
        const existingIds = new Set(r.logs.map((l) => l.id))
        const newLogs = logs.filter((l) => !existingIds.has(l.id))
        return { ...r, logs: [...r.logs, ...newLogs], status }
      }),
    })),
  addLog: (id, log) =>
    set((state) => ({
      runs: state.runs.map((r) => {
        if (r.id !== id) return r
        if (r.logs.some((l) => l.id === log.id)) return r
        return { ...r, logs: [...r.logs, log] }
      }),
    })),
  updateRunStatus: (id, status) =>
    set((state) => ({
      runs: state.runs.map((r) => (r.id === id ? { ...r, status } : r)),
    })),
  clearRuns: () => set({ runs: [], selectedLogId: null }),
}))
