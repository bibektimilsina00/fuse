import React from 'react'

interface PanelHeadProps {
  icon: React.ReactNode
  title: string
  count?: string
  action?: React.ReactNode
}

export function PanelHead({ icon, title, count, action }: PanelHeadProps) {
  return (
    <div className="panel-head">
      <div className="panel-title">
        {icon}
        <span>{title}</span>
        {count && <span className="count">{count}</span>}
      </div>
      {action && <div className="panel-actions">{action}</div>}
    </div>
  )
}
