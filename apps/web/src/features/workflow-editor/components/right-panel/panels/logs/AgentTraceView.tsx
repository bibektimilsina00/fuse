import { useState } from 'react'
import { CheckCircle2, ChevronRight, Loader2, XCircle, Wrench } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { AgentTraceStep } from '@/features/runs/store/runsStore'

interface Props {
  steps: AgentTraceStep[]
  nodeLabel: string
}

/**
 * Vertical stepper that renders an agent node's tool-call trace.
 * Each row shows the tool id, status, duration, args (collapsed) and
 * either the result or the error message. Steps update in place — a
 * `running` step flips to success/failed when the matching
 * `tool_call_completed` event arrives, with no re-layout.
 */
export function AgentTraceView({ steps, nodeLabel }: Props) {
  if (steps.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-6 py-8 text-center">
        <Wrench className="mb-2 h-5 w-5 text-[var(--text-faint)]" />
        <div className="text-[12px] font-medium text-[var(--text)]">No tool calls yet</div>
        <div className="mt-1 max-w-[280px] text-[11px] text-[var(--text-faint)]">
          {nodeLabel} hasn't executed any tools in this run. The trace will populate live as
          the agent thinks and acts.
        </div>
      </div>
    )
  }

  const totalDuration = steps.reduce((sum, s) => sum + (s.durationMs ?? 0), 0)
  const successCount = steps.filter((s) => s.status === 'success').length
  const failedCount = steps.filter((s) => s.status === 'failed').length
  const runningCount = steps.filter((s) => s.status === 'running').length

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 items-center gap-3 border-b border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2 text-[11px] text-[var(--text-mute)]">
        <span>
          <span className="font-semibold text-[var(--text)]">{steps.length}</span> calls
        </span>
        {successCount > 0 && (
          <span className="flex items-center gap-1 text-[var(--ok,#22c55e)]">
            <CheckCircle2 className="h-3 w-3" /> {successCount}
          </span>
        )}
        {failedCount > 0 && (
          <span className="flex items-center gap-1 text-[var(--err)]">
            <XCircle className="h-3 w-3" /> {failedCount}
          </span>
        )}
        {runningCount > 0 && (
          <span className="flex items-center gap-1 text-[var(--text-faint)]">
            <Loader2 className="h-3 w-3 animate-spin" /> {runningCount}
          </span>
        )}
        {totalDuration > 0 && (
          <span className="ml-auto">
            {totalDuration < 1000 ? `${totalDuration}ms` : `${(totalDuration / 1000).toFixed(2)}s`}
          </span>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-2">
        <ol className="flex flex-col gap-1.5">
          {steps.map((step, idx) => (
            <TraceStepRow key={step.id} step={step} index={idx + 1} />
          ))}
        </ol>
      </div>
    </div>
  )
}

interface RowProps {
  step: AgentTraceStep
  index: number
}

function TraceStepRow({ step, index }: RowProps) {
  const [expanded, setExpanded] = useState(false)
  const StatusIcon =
    step.status === 'running'
      ? Loader2
      : step.status === 'failed'
        ? XCircle
        : CheckCircle2
  const statusClass =
    step.status === 'failed'
      ? 'text-[var(--err)]'
      : step.status === 'running'
        ? 'text-[var(--text-faint)] animate-spin'
        : 'text-[var(--ok,#22c55e)]'

  return (
    <li
      className={cn(
        'rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] transition-colors',
        expanded && 'bg-[var(--surface-2)]',
      )}
    >
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left text-[11.5px] hover:bg-[var(--surface-2)]"
      >
        <ChevronRight
          className={cn(
            'h-3 w-3 shrink-0 text-[var(--text-faint)] transition-transform',
            expanded && 'rotate-90',
          )}
        />
        <span className="font-mono text-[10.5px] text-[var(--text-faint)]">#{index}</span>
        <StatusIcon className={cn('h-3.5 w-3.5 shrink-0', statusClass)} />
        <span className="truncate font-medium text-[var(--text)]" title={step.toolId}>
          {step.toolId}
        </span>
        {step.iteration > 0 && (
          <span className="rounded-[4px] bg-[var(--surface-3)] px-1.5 py-0.5 text-[10px] text-[var(--text-faint)]">
            iter {step.iteration}
          </span>
        )}
        <span className="ml-auto shrink-0 text-[10.5px] text-[var(--text-faint)]">
          {step.durationMs !== null
            ? step.durationMs < 1000
              ? `${step.durationMs}ms`
              : `${(step.durationMs / 1000).toFixed(2)}s`
            : '—'}
        </span>
      </button>

      {expanded && (
        <div className="border-t border-[var(--border-faint)] px-3 py-2 text-[11px] text-[var(--text-mute)]">
          {step.errorMessage && (
            <div className="mb-2 rounded-[6px] border border-[var(--err)]/30 bg-[var(--err)]/10 p-2 text-[var(--err)]">
              <div className="text-[10px] font-semibold uppercase tracking-wide">Error</div>
              <div className="mt-1 font-mono text-[11px] whitespace-pre-wrap">
                {step.errorMessage}
              </div>
            </div>
          )}

          <KeyValueBlock label="Arguments" value={step.arguments} />
          {step.status !== 'running' && (
            <KeyValueBlock label="Result" value={step.result} />
          )}

          <div className="mt-2 flex gap-3 text-[10.5px] text-[var(--text-faint)]">
            <span>Started: {formatTime(step.startedAt)}</span>
            {step.endedAt && <span>Ended: {formatTime(step.endedAt)}</span>}
          </div>
        </div>
      )}
    </li>
  )
}

function KeyValueBlock({
  label,
  value,
}: {
  label: string
  value: Record<string, unknown> | null
}) {
  const empty = value === null || (typeof value === 'object' && Object.keys(value).length === 0)
  return (
    <div className="mb-2 last:mb-0">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-[var(--text-faint)]">
        {label}
      </div>
      {empty ? (
        <div className="font-mono text-[11px] italic text-[var(--text-faint)]">empty</div>
      ) : (
        <pre className="overflow-x-auto rounded-[6px] bg-[var(--bg-2)] p-2 font-mono text-[10.5px] leading-[1.4] text-[var(--text)]">
          {JSON.stringify(value, null, 2)}
        </pre>
      )}
    </div>
  )
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}
