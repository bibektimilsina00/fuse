import { useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  MoreHorizontal, MessageCircle, Send, Play, Square, Loader2,
  LayoutDashboard, Lock, Unlock, Download, Copy, Trash2,
} from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { useReactFlow } from 'reactflow'
import { cn } from '@/lib/cn'
import { Button } from '@/shared/components'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'

interface EditorActionBarProps {
  onRun: () => void
  isRunning: boolean
}

// ── Portalled dropdown ────────────────────────────────────────────────────────

interface MenuItem {
  label: string
  icon: React.ReactNode
  onClick: () => void
  variant?: 'danger'
  dividerBefore?: boolean
}

function OptionsMenu({ anchorRect, items, onClose }: { anchorRect: DOMRect; items: MenuItem[]; onClose: () => void }) {
  const menuW = 220
  const menuH = items.length * 34 + 16
  const left = anchorRect.right - menuW
  const top = anchorRect.bottom + 4 + menuH > window.innerHeight
    ? anchorRect.top - menuH - 4
    : anchorRect.bottom + 4

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998]" onClick={onClose} />
      <div
        className="fixed z-[9999] overflow-hidden rounded-[12px] border border-[var(--border)] bg-[var(--bg-2)] p-1.5 shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]"
        style={{ left, top, width: menuW }}
      >
        {items.map((item, i) => (
          <div key={i}>
            {item.dividerBefore && <div className="my-1 h-px bg-[var(--border-faint)] mx-1" />}
            <button
              onClick={() => { item.onClick(); onClose() }}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-[7px] px-3 py-2 text-[12.5px] font-medium transition-colors [&_svg]:h-3.5 [&_svg]:w-3.5 [&_svg]:shrink-0',
                item.variant === 'danger'
                  ? 'text-[var(--err)] hover:bg-[var(--badge-err-bg)] [&_svg]:text-[var(--err)]'
                  : 'text-[var(--text)] hover:bg-[var(--surface)] [&_svg]:text-[var(--text-mute)]',
              )}
            >
              {item.icon}
              {item.label}
            </button>
          </div>
        ))}
      </div>
    </>,
    document.body,
  )
}

// ── Action bar ────────────────────────────────────────────────────────────────

export function EditorActionBar({ onRun, isRunning }: EditorActionBarProps) {
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null)
  const btnRef = useRef<HTMLButtonElement>(null)
  const navigate = useNavigate()
  const { id: workflowId } = useParams<{ id: string }>()
  const { fitView } = useReactFlow()

  const setTab = useWorkflowEditorStore(s => s.setInspectorTab)
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const edges = useWorkflowEditorStore(s => s.edges)

  const handleExport = () => {
    const data = JSON.stringify({ nodes, edges }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workflow-${workflowId ?? 'export'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const menuItems: MenuItem[] = [
    {
      label: 'Auto layout',
      icon: <LayoutDashboard />,
      onClick: () => fitView({ duration: 400, padding: 0.2 }),
    },
    {
      label: 'Lock workflow',
      icon: <Lock />,
      onClick: () => {},
      dividerBefore: true,
    },
    {
      label: 'Export workflow',
      icon: <Download />,
      onClick: handleExport,
    },
    {
      label: 'Duplicate workflow',
      icon: <Copy />,
      onClick: () => {},
    },
    {
      label: 'Delete workflow',
      icon: <Trash2 />,
      onClick: () => { if (confirm('Delete this workflow? This cannot be undone.')) navigate('/automations') },
      variant: 'danger',
      dividerBefore: true,
    },
  ]

  return (
    <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[var(--border-faint)] px-3 py-2.5">
      {/* Left: three-dots + chat */}
      <div className="flex items-center gap-1">
        <button
          ref={btnRef}
          onClick={() => setAnchorRect(btnRef.current?.getBoundingClientRect() ?? null)}
          className={cn(
            'flex h-7 w-7 items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors',
            'hover:bg-[var(--surface)] hover:text-[var(--text)]',
            anchorRect && 'bg-[var(--surface)] text-[var(--text)]',
          )}
          title="Workflow options"
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>

        <button
          onClick={() => setTab('copilot')}
          className="flex h-7 w-7 items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
          title="Open Copilot"
        >
          <MessageCircle className="h-4 w-4" />
        </button>
      </div>

      {/* Right: Deploy + Run */}
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" leftIcon={<Send className="text-[var(--accent)]" />}>
          Deploy
        </Button>

        <Button
          variant="primary"
          size="sm"
          onClick={onRun}
          disabled={isRunning}
          leftIcon={isRunning ? <Loader2 className="animate-spin" /> : <Play className="fill-current" />}
        >
          {isRunning ? 'Running' : 'Run'}
        </Button>
      </div>

      {anchorRect && (
        <OptionsMenu
          anchorRect={anchorRect}
          items={menuItems}
          onClose={() => setAnchorRect(null)}
        />
      )}
    </div>
  )
}
