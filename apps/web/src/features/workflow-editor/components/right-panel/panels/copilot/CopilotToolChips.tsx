import { Loader2, Check, AlertTriangle, Wrench, Search, FileText, GitMerge } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { ToolCall } from '../../../../hooks/useCopilotChat'

interface Props {
  calls: ToolCall[]
}

const TOOL_META: Record<string, { label: string; Icon: React.FC<{ className?: string }> }> = {
  search_node_types: { label: 'Searched nodes',   Icon: Search },
  get_node_metadata: { label: 'Read node spec',   Icon: FileText },
  edit_workflow:     { label: 'Edited workflow',  Icon: GitMerge },
}

/**
 * Small horizontal stack of tool-call chips shown above an assistant
 * message. Each chip shows a label inferred from the tool name plus a
 * status indicator (spinner / check / warning).
 */
export function CopilotToolChips({ calls }: Props) {
  if (!calls.length) return null

  return (
    <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
      {calls.map((call, i) => {
        const meta = TOOL_META[call.tool] ?? { label: call.tool, Icon: Wrench }
        return (
          <span
            key={`${call.tool}-${i}`}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full border px-2 py-[2px] text-[10.5px] font-medium',
              call.status === 'running' && 'border-[var(--border-faint)] bg-[var(--surface)] text-[var(--text-mute)]',
              call.status === 'success' && 'border-[#9ece6a]/40 bg-[#9ece6a]/10 text-[#9ece6a]',
              call.status === 'failed'  && 'border-[var(--err)]/40 bg-[var(--err)]/10 text-[var(--err)]',
            )}
            title={call.tool}
          >
            <meta.Icon className="h-3 w-3" />
            <span>{meta.label}</span>
            <StatusIcon status={call.status} />
          </span>
        )
      })}
    </div>
  )
}

function StatusIcon({ status }: { status: ToolCall['status'] }) {
  if (status === 'running') return <Loader2 className="h-3 w-3 animate-spin" />
  if (status === 'success') return <Check className="h-3 w-3" />
  return <AlertTriangle className="h-3 w-3" />
}
