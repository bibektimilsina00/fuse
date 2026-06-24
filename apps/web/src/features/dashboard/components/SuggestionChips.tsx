import { ArrowUpRight } from 'lucide-react'

interface SuggestionChipsProps {
  suggestions: string[]
  onPick: (text: string) => void
  disabled?: boolean
}

/** Linear-style suggested-automations card grid. */
export function SuggestionChips({ suggestions, onPick, disabled }: SuggestionChipsProps) {
  if (suggestions.length === 0) return null
  return (
    <div className="flex flex-col gap-[12px]">
      <div className="flex items-center gap-[8px] mx-[2px]">
        <span className="text-[11px] font-semibold tracking-[0.07em] text-[var(--text-faint)]">
          SUGGESTED AUTOMATIONS
        </span>
        <span className="flex-1 h-px bg-[var(--border-faint)]" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-[12px]">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onPick(s)}
            disabled={disabled}
            className="group text-left flex flex-col gap-[11px] py-[15px] px-[16px] rounded-[11px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.015)] transition-colors hover:bg-[rgba(255,255,255,0.045)] hover:border-[var(--border)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="flex items-center justify-end">
              <ArrowUpRight className="w-[15px] h-[15px] text-[var(--text-dim)] group-hover:text-[var(--text-mute)] transition-colors" strokeWidth={1.9} />
            </span>
            <span className="text-[13.5px] font-medium text-[var(--text)] leading-[1.4]">
              {s.length > 86 ? `${s.slice(0, 86)}…` : s}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
