import React from 'react'
import { getIcon } from '../../../utils/icon-map'

interface NodeHeaderProps {
  label: string
  icon: string
  color?: string
}

export const NodeHeader = ({ label, icon, color }: NodeHeaderProps) => (
  <div className="flex items-center gap-1.5 px-2.5 py-1 border-b border-border-faint">
    <div
      className="flex size-[14px] shrink-0 items-center justify-center rounded-[2px]"
      style={{ background: color ?? 'var(--surface-3)' }}
    >
      {React.cloneElement(getIcon(icon) as React.ReactElement, {
        className: 'size-[8px] text-white',
      })}
    </div>
    <span className="truncate text-[11px] font-semibold leading-none text-[var(--text)]" title={label}>
      {label}
    </span>
  </div>
)
