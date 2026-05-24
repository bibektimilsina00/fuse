import { Play, Square, Lock, Copy, ArrowLeftRight, ArrowUpDown, Trash2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Tooltip } from '@/shared/components'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

interface NodeToolbarProps {
  id: string
}

const btnCls = cn(
  'inline-flex size-[16px] shrink-0 items-center justify-center rounded-[4px] [&_svg]:size-[8px]',
  'bg-[var(--surface)] text-[var(--text-mute)] outline-none transition-all duration-150',
  'hover:bg-[var(--accent-soft)] hover:text-[var(--accent)]',
  'disabled:pointer-events-none disabled:opacity-40',
)

export const NodeToolbar = ({ id }: NodeToolbarProps) => {
  const nodes                    = useWorkflowEditorStore(s => s.nodes)
  const removeNode               = useWorkflowEditorStore(s => s.removeNode)
  const toggleNodeLock           = useWorkflowEditorStore(s => s.toggleNodeLock)
  const duplicateNode            = useWorkflowEditorStore(s => s.duplicateNode)
  const toggleNodeHandleDirection = useWorkflowEditorStore(s => s.toggleNodeHandleDirection)

  const node = nodes.find(n => n.id === id)
  const isLocked     = node?.data?.locked ?? false
  const isHorizontal = (node?.data?.handleDirection ?? 'horizontal') === 'horizontal'

  return (
    <div className="pointer-events-auto absolute -top-[30px] right-0 flex flex-row items-center gap-[2px] rounded-[6px] bg-[var(--bg-2)] p-[3px] opacity-0 transition-opacity duration-200 group-hover:opacity-100">
      <Tooltip content="Run node">
        <button type="button" className={btnCls}><Play /></button>
      </Tooltip>

      <Tooltip content="Stop node">
        <button type="button" className={btnCls}><Square /></button>
      </Tooltip>

      <Tooltip content={isLocked ? 'Unlock node' : 'Lock node'}>
        <button
          type="button"
          onClick={() => toggleNodeLock(id)}
          className={cn(btnCls, isLocked && 'bg-[oklch(0.78_0.14_145/0.18)] text-[var(--ok)] hover:bg-[oklch(0.78_0.14_145/0.26)] hover:text-[var(--ok)]')}
        >
          <Lock />
        </button>
      </Tooltip>

      <Tooltip content="Duplicate node">
        <button type="button" onClick={() => duplicateNode(id)} className={btnCls}><Copy /></button>
      </Tooltip>

      <Tooltip content={isHorizontal ? 'Vertical handles' : 'Horizontal handles'}>
        <button type="button" onClick={() => toggleNodeHandleDirection(id)} className={btnCls}>
          {isHorizontal ? <ArrowUpDown /> : <ArrowLeftRight />}
        </button>
      </Tooltip>

      <Tooltip content="Delete node">
        <button
          type="button"
          onClick={() => removeNode(id)}
          className={cn(btnCls, 'hover:bg-[oklch(0.70_0.18_22/0.18)] hover:text-[var(--err)]')}
        >
          <Trash2 />
        </button>
      </Tooltip>
    </div>
  )
}
