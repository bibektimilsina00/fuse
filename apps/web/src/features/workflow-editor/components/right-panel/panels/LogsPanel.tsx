import { useMemo, useState } from 'react'
import { CheckCircle2, Loader2, Terminal, Trash2, XCircle } from 'lucide-react'
import { Empty } from '@/shared/components'
import { useRunsStore, useWorkflowRuns, type RunLog } from '@/features/runs/store/runsStore'
import { useRunStream } from '@/features/runs/hooks/useRunStream'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import {
  ErrorView,
  JsonInspector,
  LogRow,
  isNodeCompletionLog,
  type NodeInfo,
  type Tab,
} from './logs'

/**
 * Logs panel — split view: a `Runs` list on the left, an inspector on the
 * right that shows either the JSON tree/code of the selected log's
 * input/output or, for failed nodes, an `ErrorView` with a "Fix with
 * Copilot" call-to-action.
 *
 * The panel reads execution data from `useWorkflowRuns(workflowId)` — runs
 * are scoped per workflow so switching workflows preserves history.
 */
export function LogsPanel() {
  const workflowId = useWorkflowEditorStore((s) => s.workflow?.id ?? null)
  const slice = useWorkflowRuns(workflowId)
  const { runs, activeExecutionId, selectedLogId } = slice
  const setSelectedLogId = useRunsStore((s) => s.setSelectedLogId)
  const clearRuns = useRunsStore((s) => s.clearRuns)
  const setActiveExecutionId = useRunsStore((s) => s.setActiveExecutionId)

  const nodes = useWorkflowEditorStore((s) => s.nodes)
  const nodeDefinitions = useWorkflowEditorStore((s) => s.nodeDefinitions)
  const selectNode = useWorkflowEditorStore((s) => s.setSelectedNodeId)

  useRunStream(workflowId, activeExecutionId)

  const [tab, setTab] = useState<Tab>('output')

  const nodeInfoById = useMemo(() => {
    const map = new Map<string, NodeInfo>()
    for (const n of nodes) {
      const def = nodeDefinitions.find((d) => d.type === n.type)
      const label = (n.data?.label as string | undefined) || def?.name || n.id
      map.set(n.id, {
        label,
        icon: def?.icon ?? 'Box',
        color: def?.color,
      })
    }
    return map
  }, [nodes, nodeDefinitions])

  const selectedLog = useMemo<RunLog | null>(() => {
    if (!selectedLogId) return null
    for (const r of runs) {
      const l = r.logs.find((x) => x.id === selectedLogId)
      if (l) return l
    }
    return null
  }, [selectedLogId, runs])

  const visible = useMemo(() => {
    if (!selectedLog) return null
    if (tab === 'output') {
      return (selectedLog.payload?.output as unknown) ?? (selectedLog.payload?.error as unknown) ?? null
    }
    return (selectedLog.payload?.input as unknown) ?? (selectedLog.payload?.data_in as unknown) ?? null
  }, [selectedLog, tab])

  if (runs.length === 0) {
    return (
      <Empty
        icon={<Terminal />}
        title="No run logs"
        description="Run the workflow to see execution logs here."
        className="h-full"
      />
    )
  }

  return (
    <div className="flex h-full min-h-0">
      <RunsList
        runs={runs}
        selectedLogId={selectedLogId}
        nodeInfoById={nodeInfoById}
        onSelectLog={(log) => {
          if (workflowId) setSelectedLogId(workflowId, log.id)
          if (log.nodeId) selectNode(log.nodeId)
        }}
        onClear={() => {
          if (!workflowId) return
          clearRuns(workflowId)
          setActiveExecutionId(workflowId, null)
        }}
      />

      <SelectedLogView
        selectedLog={selectedLog}
        nodeInfoById={nodeInfoById}
        tab={tab}
        setTab={setTab}
        payload={visible}
      />
    </div>
  )
}

// ── Runs list ────────────────────────────────────────────────────────────────

interface RunsListProps {
  runs: { executionId: string; status: string; logs: RunLog[] }[]
  selectedLogId: string | null
  nodeInfoById: Map<string, NodeInfo>
  onSelectLog: (log: RunLog) => void
  onClear: () => void
}

function RunsList({
  runs, selectedLogId, nodeInfoById, onSelectLog, onClear,
}: RunsListProps) {
  return (
    <div className="flex w-[240px] shrink-0 flex-col border-r border-[var(--border-faint)]">
      <div className="flex h-[36px] shrink-0 items-center justify-between border-b border-[var(--border-faint)] px-3 py-1.5">
        <span className="text-[12px] font-medium text-[var(--text)]">Runs</span>
        <button
          onClick={onClear}
          className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11.5px] text-[var(--text-mute)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          title="Clear runs"
        >
          <Trash2 className="h-3 w-3" /> Clear
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {runs
          .map((run, runIdx) => ({ run, runNumber: runIdx + 1 }))
          .slice()
          .reverse()
          .map(({ run, runNumber }) => {
            const completions = run.logs.filter(isNodeCompletionLog)
            return (
              <div key={run.executionId} className="mb-4 last:mb-0">
                <div className="flex items-center gap-2 px-1 pb-1">
                  {run.status === 'running' ? (
                    <Loader2 className="h-3 w-3 animate-spin text-[var(--text-faint)]" />
                  ) : run.status === 'failed' ? (
                    <XCircle className="h-3 w-3 text-[var(--err)]" />
                  ) : (
                    <CheckCircle2 className="h-3 w-3 text-[var(--ok,#22c55e)]" />
                  )}
                  <span className="text-[11px] font-semibold text-[var(--text-mute)]">
                    Run #{runNumber}
                  </span>
                  <span className="text-[10.5px] text-[var(--text-faint)]">{run.status}</span>
                </div>
                {completions.length === 0 ? (
                  <div className="px-2 py-1 text-[11.5px] italic text-[var(--text-faint)]">
                    {run.status === 'running' ? 'Executing…' : 'No node logs'}
                  </div>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {completions.map((log) => {
                      const info = nodeInfoById.get(log.nodeId!) ?? {
                        label: log.message || log.nodeId!,
                        icon: 'Box',
                      }
                      return (
                        <LogRow
                          key={log.id}
                          log={log}
                          selected={selectedLogId === log.id}
                          nodeInfo={info}
                          onClick={() => onSelectLog(log)}
                        />
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
      </div>
    </div>
  )
}

// ── Selected-log view ────────────────────────────────────────────────────────

interface SelectedLogViewProps {
  selectedLog: RunLog | null
  nodeInfoById: Map<string, NodeInfo>
  tab: Tab
  setTab: (t: Tab) => void
  payload: unknown
}

function SelectedLogView({
  selectedLog, nodeInfoById, tab, setTab, payload,
}: SelectedLogViewProps) {
  if (!selectedLog) {
    return (
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex shrink-0 items-center gap-1 border-b border-[var(--border-faint)] px-3 py-1.5">
          <span className="px-1 text-[11.5px] text-[var(--text-faint)]">
            Select a node to view its details.
          </span>
        </div>
      </div>
    )
  }

  const info: NodeInfo = (selectedLog.nodeId && nodeInfoById.get(selectedLog.nodeId)) || {
    label: selectedLog.message || selectedLog.nodeId || 'Log',
    icon: 'Box',
  }
  const errored = !!selectedLog.payload && 'error' in (selectedLog.payload as Record<string, unknown>)

  if (errored && tab === 'output' && selectedLog.nodeId) {
    return (
      <div className="flex min-w-0 flex-1 flex-col">
        <ErrorView log={selectedLog} nodeInfo={info} tab={tab} onTabChange={setTab} />
      </div>
    )
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <JsonInspector
        payload={payload}
        nodeId={selectedLog.nodeId}
        tab={tab}
        onTabChange={setTab}
        downloadName={`${selectedLog.nodeId || 'log'}-${tab}`}
      />
    </div>
  )
}
