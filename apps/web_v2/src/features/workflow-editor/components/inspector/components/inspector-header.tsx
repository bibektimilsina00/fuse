import { X } from 'lucide-react'
import { Badge, Button, Input } from '@/shared/components'
import type { NodeDefinition } from '../../../types/editorTypes'
import { getIcon } from '../../../utils/icon-map'

interface InspectorHeaderProps {
  nodeId: string
  label: string
  definition: NodeDefinition
  onLabelChange: (label: string) => void
  onClose: () => void
}

export function InspectorHeader({ nodeId, label, definition, onLabelChange, onClose }: InspectorHeaderProps) {
  const Icon = getIcon(definition.icon)

  return (
    <header className="shrink-0 border-b border-[var(--border-faint)] bg-[var(--bg-2)] px-4 py-3">
      <div className="flex items-start gap-3">
        <div
          className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-[7px] text-white [&_svg]:h-3.5 [&_svg]:w-3.5"
          style={{ background: definition.color ?? 'var(--surface-3)' }}
        >
          {Icon}
        </div>
        <div className="min-w-0 flex-1">
          <Input
            key={nodeId}
            defaultValue={label}
            onBlur={event => {
              const nextLabel = event.target.value.trim()
              if (nextLabel && nextLabel !== label) onLabelChange(nextLabel)
            }}
            onKeyDown={event => {
              if (event.key === 'Enter') event.currentTarget.blur()
            }}
            className="h-8 px-2 text-[13px]"
            aria-label="Node name"
          />
          <div className="mt-2 flex items-center gap-2">
            <Badge variant="draft" className="normal-case tracking-normal">{definition.category}</Badge>
            <span className="truncate font-mono text-[10px] text-[var(--text-faint)]">{nodeId}</span>
          </div>
        </div>
        <Button variant="icon-sm" type="button" title="Close inspector" onClick={onClose}>
          <X />
        </Button>
      </div>
    </header>
  )
}
