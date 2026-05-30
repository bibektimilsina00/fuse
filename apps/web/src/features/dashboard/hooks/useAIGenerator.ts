import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/shared/components'
import { workflowAPI } from '@/features/workflows/services/workflowAPI'
import { workflowKeys } from '@/features/workflows/hooks/keys'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { streamCopilotChat } from '@/features/workflow-editor/services/copilotAPI'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'

const LOADING_MESSAGES = [
  'Reading your request…',
  'Discovering the right nodes…',
  'Drafting the workflow…',
  'Wiring the connections…',
  'Validating fields…',
  'Tightening the bolts…',
  'Almost there…',
]
const MESSAGE_INTERVAL_MS = 1800

/**
 * Owns the dashboard's "type a prompt → get a built workflow" flow:
 * create workflow → stream Copilot → persist proposed graph → navigate. Surfaces
 * a rotating status message + cancel so the page stays presentational.
 */
export function useAIGenerator() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { toast } = useToast()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const [creating, setCreating] = useState(false)
  const [msgIdx, setMsgIdx] = useState(0)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!creating) return
    const id = setInterval(
      () => setMsgIdx(i => (i + 1) % LOADING_MESSAGES.length),
      MESSAGE_INTERVAL_MS,
    )
    return () => clearInterval(id)
  }, [creating])

  const generate = async (prompt: string) => {
    setMsgIdx(0)
    setCreating(true)
    let createdId: string | null = null
    try {
      const name = prompt.slice(0, 60).trim() || 'New AI workflow'
      const wf = await workflowAPI.create({ name })
      createdId = wf.id

      const controller = new AbortController()
      abortRef.current = controller

      let proposed: { nodes: unknown[]; edges: unknown[] } | null = null
      const stream = streamCopilotChat(
        wf.id,
        { messages: [{ role: 'user', content: prompt }], graph: { nodes: [], edges: [] } },
        controller.signal,
      )
      for await (const ev of stream) {
        if (ev.type === 'workflow_proposed') {
          proposed = ev.graph as { nodes: unknown[]; edges: unknown[] }
        } else if (ev.type === 'error') {
          throw new Error(String(ev.message ?? 'Copilot error'))
        }
      }

      if (proposed) {
        // Fresh workflow → version_vector starts at 0.
        await editorAPI.saveGraph(wf.id, proposed, 0).catch(() => {})
      }
      qc.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
      navigate(`/workflows/${wf.id}`)
    } catch (e) {
      const err = e as Error
      if (err.name === 'AbortError') {
        if (createdId) navigate(`/workflows/${createdId}`)
      } else {
        toast(`Copilot failed: ${err.message || 'error'}`, { variant: 'err' })
      }
    } finally {
      abortRef.current = null
      setCreating(false)
    }
  }

  const cancel = () => abortRef.current?.abort()

  return {
    creating,
    message: LOADING_MESSAGES[msgIdx],
    generate,
    cancel,
  }
}
