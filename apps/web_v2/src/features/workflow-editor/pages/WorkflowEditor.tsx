import { useParams, useNavigate } from 'react-router-dom'
import { useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowEditor } from '../hooks/useWorkflowEditor'
import { EditorTopbar }  from '../components/EditorTopbar'
import { EditorCanvas }  from '../components/EditorCanvas'

export function WorkflowEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()

  const {
    workflow,
    isLoading,
    error,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    run,
    rename,
    toggle,
    isRunning,
    saveState,
  } = useWorkflowEditor(id ?? '')

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[var(--bg)]">
        <div className="w-8 h-8 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !workflow) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-[var(--bg)] gap-4">
        <p className="text-[14px] text-[var(--err)]">Failed to load workflow</p>
        <button
          onClick={() => navigate(APP_ROUTES.AUTOMATIONS)}
          className="btn btn-secondary"
        >
          Back to automations
        </button>
      </div>
    )
  }

  const handleRun = () => {
    run(undefined, {
      onSuccess: (res) => toast('Workflow triggered', { variant: 'ok', description: `Execution ${res.execution_id.slice(0, 8)}… started` }),
      onError: (err) => toast('Failed to run', { variant: 'err', description: err instanceof Error ? err.message : 'Try again.' }),
    })
  }

  return (
    <div className="flex flex-col h-full w-full bg-[var(--bg)] overflow-hidden">
      <EditorTopbar
        workflow={workflow}
        saveState={saveState}
        isRunning={isRunning}
        onRename={rename}
        onToggle={() => toggle()}
        onRun={handleRun}
      />

      <div className="flex flex-1 min-h-0">
        <EditorCanvas
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
        />
      </div>
    </div>
  )
}
