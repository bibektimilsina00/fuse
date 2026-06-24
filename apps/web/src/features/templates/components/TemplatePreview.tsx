import { Workflow as WorkflowIcon } from 'lucide-react'

/**
 * Replaces the static "inspo-mock" placeholder inside the card art. Shows
 * up to 5 tool/integration chips derived from the template's
 * `tools_required` list plus a node count badge. Falls back to a clean
 * mock with the kind label when no tools metadata is present.
 *
 * Kept inside the `.inspo-art` panel so the card's outer dimensions +
 * layout stay identical to the original design — only the inner mock
 * graphic changes.
 */

interface TemplatePreviewProps {
  tools: string[]
  steps: number
  kind: string
}

export function TemplatePreview({ tools, steps, kind }: TemplatePreviewProps) {
  const visible = tools.slice(0, 5)
  const extra = Math.max(0, tools.length - visible.length)

  return (
    <div className="absolute inset-x-[12%] bottom-[-12%] top-[28%] flex flex-col overflow-hidden rounded-[10px_10px_0_0] border border-[var(--border)] bg-[var(--bg-2)] shadow-[0_-8px_24px_-12px_oklch(0_0_0/0.4)]">
      {/* Title bar */}
      <div className="flex h-[18px] shrink-0 items-center gap-1 border-b border-[var(--border-faint)] bg-[var(--surface)] px-2">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--err)]/60" />
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--warn)]/60" />
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--ok)]/60" />
        <span className="ml-auto font-mono text-[8px] uppercase tracking-[0.08em] text-[var(--text-faint)]">
          {kind}
        </span>
      </div>

      {/* Body — either tool chips or the abstract pattern fallback */}
      <div className="flex flex-1 min-h-0 flex-col gap-1 p-2">
        {visible.length > 0 ? (
          <div className="flex flex-wrap content-start gap-1">
            {visible.map((tool) => (
              <span
                key={tool}
                className="rounded-[4px] border border-[var(--border-faint)] bg-[var(--bg)] px-1.5 py-0.5 font-mono text-[8.5px] uppercase tracking-[0.04em] text-[var(--text-mute)]"
              >
                {tool}
              </span>
            ))}
            {extra > 0 && (
              <span className="rounded-[4px] bg-[var(--accent)]/15 px-1.5 py-0.5 font-mono text-[8.5px] font-bold uppercase tracking-[0.04em] text-[var(--accent)]">
                +{extra}
              </span>
            )}
          </div>
        ) : (
          // Visual fallback for templates that don't surface tools (e.g.
          // pure logic flows). Mirrors the dashboard cards' empty-state
          // dot pattern so the marketplace stays visually consistent.
          <div className="flex flex-1 items-center justify-center text-[var(--text-faint)]">
            <WorkflowIcon className="h-5 w-5" />
          </div>
        )}

        <div className="mt-auto flex items-center justify-between gap-2 border-t border-[var(--border-faint)] pt-1 font-mono text-[9px] uppercase tracking-[0.06em] text-[var(--text-faint)]">
          <span>{steps} nodes</span>
          <span className="h-[3px] w-[3px] rounded-full bg-[var(--ok)]" />
        </div>
      </div>
    </div>
  )
}
