import { useState } from 'react'
import { AlertOctagon, AlertTriangle, CheckCircle2, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/cn'
import { parseStructuredError } from '../../../right-panel/panels/logs/structuredError'

interface Props {
  /**
   * Error text from an API call. Detected and rendered structured if it
   * starts with the backend `__fuse_err_v1__` sentinel; otherwise
   * displayed verbatim as a one-line red string.
   */
  error: string
  /**
   * Layout density. Pickers / inline dropdowns pass `compact` for a
   * smaller card. Full-panel callers omit it for a roomier card.
   */
  compact?: boolean
}

/**
 * Inline structured-error display for non-inspector surfaces — pickers,
 * dropdowns, sidebar panels, anywhere we have to show a backend error
 * outside the run-log inspector.
 *
 * The renderer auto-detects sentinel-prefixed structured payloads
 * emitted by `make_structured_error(...)` on the backend and shows the
 * title + summary + bulleted actions + collapsible raw body. Plain
 * strings fall through to the existing one-line red text.
 *
 * Reuse this anywhere you'd otherwise write
 * `<div className="text-err">{error}</div>` so the rich error UX
 * shows up automatically when the backend opts in.
 */
export function ApiErrorMessage({ error, compact }: Props) {
  const structured = parseStructuredError(error)
  const [showRaw, setShowRaw] = useState(false)

  if (!structured) {
    return (
      <div
        className={cn(
          'text-[var(--err,#dc2626)]',
          compact ? 'px-2 py-2 text-[11.5px]' : 'px-3 py-3 text-[12px]',
        )}
      >
        {error}
      </div>
    )
  }

  const isWarning = structured.severity === 'warning'
  const Icon = isWarning ? AlertTriangle : AlertOctagon
  const tint = isWarning ? 'rgba(234,179,8,0.06)' : 'rgba(239,68,68,0.06)'
  const accent = isWarning ? 'var(--warn,#eab308)' : 'var(--err,#ef4444)'

  return (
    <div className={cn('flex flex-col gap-2', compact ? 'p-2' : 'p-3')}>
      <div
        className="flex items-start gap-2 rounded-[6px] border border-[var(--border-faint)] p-2.5"
        style={{ background: tint }}
      >
        <Icon className="mt-[1px] h-3.5 w-3.5 shrink-0" style={{ color: accent }} />
        <div className="min-w-0 flex-1">
          <div className="text-[12px] font-semibold leading-snug text-[var(--text)]">
            {structured.title}
          </div>
          {structured.summary && (
            <p className="mt-1 text-[11.5px] leading-relaxed text-[var(--text-mute)]">
              {structured.summary}
            </p>
          )}
        </div>
      </div>

      {structured.actions.length > 0 && (
        <div className="rounded-[6px] border border-[var(--border-faint)] bg-[var(--surface)] p-2.5">
          <div className="text-[10.5px] font-semibold uppercase tracking-wide text-[var(--text-mute)]">
            What to do
          </div>
          <ul className="mt-1.5 flex flex-col gap-1">
            {structured.actions.map((action, i) => (
              <li
                key={i}
                className="flex items-start gap-1.5 text-[11.5px] leading-snug text-[var(--text)]"
              >
                <CheckCircle2
                  className="mt-[2px] h-3 w-3 shrink-0 text-[var(--text-faint)]"
                  aria-hidden
                />
                <span className="min-w-0 flex-1">{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {structured.raw && (
        <div className="rounded-[6px] border border-[var(--border-faint)] bg-[var(--surface)]">
          <button
            type="button"
            onClick={() => setShowRaw((v) => !v)}
            className={cn(
              'flex w-full items-center gap-1.5 rounded-t-[6px] px-2.5 py-1.5 text-left',
              'text-[10.5px] font-medium uppercase tracking-wide text-[var(--text-mute)]',
              'transition-colors hover:bg-[var(--surface-2)]',
              !showRaw && 'rounded-b-[6px]',
            )}
          >
            <ChevronDown
              className={cn(
                'h-3 w-3 shrink-0 transition-transform',
                !showRaw && '-rotate-90',
              )}
            />
            Raw response
          </button>
          {showRaw && (
            <pre
              className={cn(
                'max-h-[200px] overflow-auto whitespace-pre-wrap break-all border-t border-[var(--border-faint)]',
                'px-2.5 py-2 text-[10.5px] leading-relaxed text-[var(--text-mute)]',
              )}
            >
              {structured.raw}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
