import React from 'react'
import { cn } from '@/lib/cn'

interface Props {
  icon: React.ReactNode
  title: string
  onClick: () => void
  active?: boolean
  disabled?: boolean
  btnRef?: React.Ref<HTMLButtonElement>
}

/**
 * Square 24×24 icon button used across the logs inspector toolbar.
 *
 * `active` paints the button as if it's a toggle in its on state — e.g. the
 * Wrap toggle. Disabled buttons fade to 40% and stop reacting to hover.
 */
export function IconBtn({ icon, title, onClick, active, disabled, btnRef }: Props) {
  return (
    <button
      ref={btnRef}
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={cn(
        'flex h-6 w-6 items-center justify-center rounded-sm transition-colors',
        active
          ? 'bg-[var(--surface-2)] text-[var(--text)]'
          : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
        disabled && 'cursor-default opacity-40 hover:bg-transparent hover:text-[var(--text-mute)]',
      )}
    >
      {icon}
    </button>
  )
}
