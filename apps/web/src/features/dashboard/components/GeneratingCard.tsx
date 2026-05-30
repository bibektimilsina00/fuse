import { Loader2, X } from 'lucide-react'

interface GeneratingCardProps {
  message: string
  onCancel: () => void
}

/** Inline placeholder shown while Copilot drafts the workflow. */
export function GeneratingCard({ message, onCancel }: GeneratingCardProps) {
  return (
    <div className="flex items-center gap-3 rounded-[12px] border border-[var(--accent-line)] bg-[var(--accent-line)]/10 px-[18px] py-4">
      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-[var(--accent)]" />
      <span className="flex-1 text-[13.5px] text-[var(--text)] transition-opacity duration-300">
        {message}
      </span>
      <button
        onClick={onCancel}
        title="Cancel"
        className="inline-flex h-7 w-7 items-center justify-center rounded-[7px] text-[var(--text-mute)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
