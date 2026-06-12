import { RotateCcw } from 'lucide-react'
import type { ReactNode } from 'react'
import type { NodeProperty } from '../../../types/editorTypes'

interface FieldWrapperProps {
  prop: NodeProperty
  /** When `canReset` + onReset are both set, renders a small reset chevron. */
  canReset?: boolean
  onReset?: () => void
  children: ReactNode
}

export function FieldWrapper({
  prop,
  canReset,
  onReset,
  children,
}: FieldWrapperProps) {
  const isRequired = prop.required === true

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <label className="text-[11px] font-semibold uppercase tracking-wide text-text-mute leading-none">
          {prop.label}
          {isRequired && <span className="ml-1 text-err">*</span>}
        </label>
        {canReset && onReset && (
          <button
            type="button"
            onClick={onReset}
            title="Reset to default"
            className="h-[18px] shrink-0 rounded px-1 text-text-faint transition-colors hover:bg-surface hover:text-text-mute"
          >
            <RotateCcw className="h-[11px] w-[11px]" />
          </button>
        )}
      </div>

      {children}

      {prop.description && (
        <p className="text-[11px] leading-relaxed text-text-faint">{prop.description}</p>
      )}
    </div>
  )
}
