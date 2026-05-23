import { Play, Square, Lock, Copy, ArrowLeftRight, ArrowUpDown, Trash2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

interface NodeToolbarProps {
  id: string
}

const buttonClass = cn(
  'inline-flex h-[24px] w-[24px] items-center justify-center rounded-[7px] border border-[var(--border-faint)]',
  'bg-transparent text-[var(--text-mute)] outline-none transition-[background,border-color,color,transform] duration-[120ms]',
  'hover:border-[var(--border-soft)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
  'active:scale-[0.97] focus-visible:ring-2 focus-visible:ring-[var(--accent)]/40',
  '[&_svg]:h-[12px] [&_svg]:w-[12px]',
)

export const NodeToolbar = ({ id }: NodeToolbarProps) => {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const removeNode = useWorkflowEditorStore(s => s.removeNode)
  const toggleNodeLock = useWorkflowEditorStore(s => s.toggleNodeLock)
  const duplicateNode = useWorkflowEditorStore(s => s.duplicateNode)
  const toggleNodeHandleDirection = useWorkflowEditorStore(s => s.toggleNodeHandleDirection)

  const node = nodes.find(n => n.id === id)
  const isLocked = node?.data?.locked ?? false
  const isHorizontal = (node?.data?.handleDirection ?? 'horizontal') === 'horizontal'

  return (
    <div className="
      pointer-events-auto absolute -top-[46px] right-0
      flex flex-row items-center gap-[5px] p-[5px]
      rounded-[11px] border border-[var(--border-faint)] bg-[var(--bg-2)] shadow-[var(--shadow-float)]
      opacity-0 transition-opacity duration-[120ms] group-hover:opacity-100
    ">
      <button type="button" title="Run node" aria-label="Run node" className={buttonClass}>
        <Play />
      </button>
      <button type="button" title="Stop node" aria-label="Stop node" className={buttonClass}>
        <Square />
      </button>

      <button
        type="button"
        title={isLocked ? 'Unlock node' : 'Lock node'}
        aria-label={isLocked ? 'Unlock node' : 'Lock node'}
        onClick={() => toggleNodeLock(id)}
        className={cn(
          buttonClass,
          isLocked && [
            'border-[oklch(0.78_0.14_145/0.25)] bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]',
            'hover:border-[oklch(0.78_0.14_145/0.3)] hover:bg-[oklch(0.78_0.14_145/0.18)] hover:text-[var(--ok)]',
          ],
        )}
      >
        <Lock />
      </button>

      <button
        type="button"
        title="Duplicate node"
        aria-label="Duplicate node"
        onClick={() => duplicateNode(id)}
        className={buttonClass}
      >
        <Copy />
      </button>

      <button
        type="button"
        title={isHorizontal ? 'Vertical handles' : 'Horizontal handles'}
        aria-label={isHorizontal ? 'Vertical handles' : 'Horizontal handles'}
        onClick={() => toggleNodeHandleDirection(id)}
        className={buttonClass}
      >
        {isHorizontal ? <ArrowUpDown /> : <ArrowLeftRight />}
      </button>

      <button
        type="button"
        title="Delete node"
        aria-label="Delete node"
        className={cn(
          buttonClass,
          'text-[var(--err)] hover:border-[oklch(0.70_0.18_22/0.25)] hover:bg-[oklch(0.70_0.18_22/0.10)] hover:text-[var(--err)]',
        )}
        onClick={() => removeNode(id)}
      >
        <Trash2 />
      </button>
    </div>
  )
}
