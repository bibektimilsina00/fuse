import { useEffect, useRef, useState } from 'react'
import { Pencil } from 'lucide-react'
import type { NodeDefinition } from '../../../types/editorTypes'
import { getIcon } from '../../../utils/icon-map'

interface InspectorHeaderProps {
  label: string
  definition: NodeDefinition
  /** Returns the user-facing error string when the new label is rejected
   *  (empty or duplicate), or `null` when the rename was applied. */
  onLabelChange: (label: string) => string | null
}

export function InspectorHeader({ label, definition, onLabelChange }: InspectorHeaderProps) {
  const Icon = getIcon(definition.icon)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(label)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Effect-based focus: deterministic across React batching, no setTimeout race.
  useEffect(() => {
    if (editing) inputRef.current?.select()
  }, [editing])

  const startEdit = () => {
    setDraft(label)
    setError(null)
    setEditing(true)
  }

  const commit = () => {
    const trimmed = draft.trim()
    if (!trimmed || trimmed === label) {
      setEditing(false)
      setError(null)
      return
    }
    const rejection = onLabelChange(trimmed)
    if (rejection) {
      // Keep the editor open so the user can fix the input. Surface the reason
      // inline rather than via toast so it can't be missed.
      setError(rejection)
      return
    }
    setEditing(false)
    setError(null)
  }

  return (
    <header className="shrink-0 border-b border-[var(--border-faint)] bg-[var(--surface)]/20 px-4 py-3">
      <div className="flex items-center gap-3">
        <div
          className="flex h-7.5 w-7.5 shrink-0 items-center justify-center rounded-sm text-white [&_svg]:h-4 [&_svg]:w-4 shadow-sm"
          style={{ background: definition.color ?? 'var(--surface-3)' }}
        >
          {Icon}
        </div>

        <div className="min-w-0 flex-1">
          {editing ? (
            <input
              ref={inputRef}
              value={draft}
              onChange={e => {
                setDraft(e.target.value)
                if (error) setError(null)
              }}
              onBlur={commit}
              onKeyDown={e => {
                if (e.key === 'Enter') commit()
                if (e.key === 'Escape') {
                  setEditing(false)
                  setError(null)
                }
              }}
              className="w-full bg-transparent text-[13px] font-semibold text-[var(--text)] outline-none border-b border-[var(--accent)] pb-0.5"
              aria-label="Node name"
              aria-invalid={!!error}
            />
          ) : (
            <div className="flex flex-col leading-tight">
              <span className="block truncate text-[13px] font-semibold text-[var(--text)]">
                {label}
              </span>
              <span className="block truncate text-[10px] uppercase tracking-wider text-[var(--text-dim)] font-semibold mt-0.5">
                {definition.name}
              </span>
            </div>
          )}
        </div>

        <button
          onClick={startEdit}
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded px-1 text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text-mute)]"
          title="Rename node"
        >
          <Pencil className="h-3 w-3" />
        </button>
      </div>

      {error && (
        <p
          role="alert"
          className="mt-1.5 text-[11px] text-[var(--err)] font-medium"
        >
          {error}
        </p>
      )}
    </header>
  )
}
