import React, { Fragment, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/cn'

export interface OverflowItem {
  label: string
  icon?: React.ReactNode
  onClick: () => void
  disabled?: boolean
  dividerBefore?: boolean
}

interface Props {
  anchorRect: DOMRect
  items: OverflowItem[]
  onClose: () => void
}

const MENU_W = 220

/**
 * Floating dropdown menu portalled to <body>. Closes on outside pointerdown
 * (capture phase, so it isn't swallowed by panes that stop propagation) and
 * on Escape.
 */
export function OverflowMenu({ anchorRect, items, onClose }: Props) {
  useEffect(() => {
    const onDown = (e: PointerEvent) => {
      const target = e.target as HTMLElement | null
      if (target?.closest('[data-overflow-menu]')) return
      onClose()
    }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('pointerdown', onDown, true)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onDown, true)
      document.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  const left = Math.max(8, Math.min(window.innerWidth - MENU_W - 8, anchorRect.right - MENU_W))
  const top = anchorRect.bottom + 4

  return createPortal(
    <div
      data-overflow-menu
      className="fixed z-[9999] rounded-md border border-[var(--border)] bg-[var(--bg-2)] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]"
      style={{ left, top, width: MENU_W }}
    >
      {items.map((item, i) => (
        <Fragment key={i}>
          {item.dividerBefore && <div className="my-[5px] h-px bg-[var(--border-faint)]" />}
          <button
            type="button"
            disabled={item.disabled}
            onClick={() => { if (!item.disabled) { item.onClick(); onClose() } }}
            className={cn(
              'flex w-full items-center gap-2 rounded-sm px-2.5 py-[6px] text-left text-[12px] font-medium transition-colors text-[var(--text)] hover:bg-[var(--surface-2)]',
              item.disabled && 'cursor-default opacity-35 hover:bg-transparent',
            )}
          >
            {item.icon && (
              <span className="flex h-3.5 w-3.5 items-center justify-center text-[var(--text-mute)]">
                {item.icon}
              </span>
            )}
            <span className="flex-1">{item.label}</span>
          </button>
        </Fragment>
      ))}
    </div>,
    document.body,
  )
}
