import { create } from 'zustand'
import type { Node, Edge } from 'reactflow'
import { useWorkflowEditorStore } from './workflowEditorStore'
import { editorAPI } from '../services/editorAPI'

interface ProposedGraph {
  nodes: Node[]
  edges: Edge[]
}

interface DiffSummary {
  added: string[]
  edited: string[]
  deleted: string[]
}

interface CopilotDiffState {
  active: boolean
  proposed: ProposedGraph | null
  baseline: ProposedGraph | null
  summary: DiffSummary | null
  proposedName: string | null
  setProposal: (graph: ProposedGraph, name?: string | null) => void
  accept: () => Promise<void>
  reject: () => void
}

function diffNodes(baseNodes: Node[], proposedNodes: Node[]): DiffSummary {
  const baseById = new Map(baseNodes.map(n => [n.id, n]))
  const propIds = new Set(proposedNodes.map(n => n.id))
  const added: string[] = []
  const edited: string[] = []
  const deleted: string[] = []
  for (const n of proposedNodes) {
    const base = baseById.get(n.id)
    if (!base) added.push(n.id)
    else if (JSON.stringify(base.data) !== JSON.stringify(n.data)) edited.push(n.id)
  }
  for (const n of baseNodes) if (!propIds.has(n.id)) deleted.push(n.id)
  return { added, edited, deleted }
}

// Holds a copilot-proposed graph as a pending diff. Accept applies it to the
// editor store (then the normal versioned autosave persists); reject discards.
export const useCopilotDiffStore = create<CopilotDiffState>((set, get) => ({
  active: false,
  proposed: null,
  baseline: null,
  summary: null,
  proposedName: null,

  setProposal: (graph, name) => {
    const editor = useWorkflowEditorStore.getState()
    const summary = diffNodes(editor.nodes, graph.nodes || [])
    const trimmedName = typeof name === 'string' ? name.trim() : ''
    const nameChange = trimmedName && trimmedName !== editor.workflow?.name
    if (!summary.added.length && !summary.edited.length && !summary.deleted.length && !nameChange) {
      set({ active: false, proposed: null, baseline: null, summary: null, proposedName: null })
      return
    }
    set({
      active: true,
      proposed: graph,
      baseline: { nodes: editor.nodes, edges: editor.edges },
      summary,
      proposedName: nameChange ? trimmedName : null,
    })
  },

  accept: async () => {
    const { proposed, proposedName } = get()
    if (!proposed) return
    const editor = useWorkflowEditorStore.getState()
    editor.pushHistory()
    editor.setNodes(proposed.nodes || [])
    editor.setEdges((proposed.edges || []).map(e => ({ ...e, type: e.type || 'custom' })))
    set({ active: false, proposed: null, baseline: null, summary: null, proposedName: null })
    if (proposedName && editor.workflow?.id) {
      try {
        const updated = await editorAPI.rename(editor.workflow.id, proposedName)
        useWorkflowEditorStore.getState().setWorkflow(updated)
      } catch {
        // Rename failure leaves graph accepted; topbar still shows old name.
      }
    }
  },

  reject: () => set({ active: false, proposed: null, baseline: null, summary: null, proposedName: null }),
}))
