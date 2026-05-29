import { create } from 'zustand'
import type { Node, Edge } from 'reactflow'
import { useWorkflowEditorStore } from './workflowEditorStore'

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
  summary: DiffSummary | null
  setProposal: (graph: ProposedGraph) => void
  accept: () => void
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
  summary: null,

  setProposal: (graph) => {
    const editor = useWorkflowEditorStore.getState()
    const summary = diffNodes(editor.nodes, graph.nodes || [])
    if (!summary.added.length && !summary.edited.length && !summary.deleted.length) {
      set({ active: false, proposed: null, summary: null })
      return
    }
    set({ active: true, proposed: graph, summary })
  },

  accept: () => {
    const { proposed } = get()
    if (!proposed) return
    const editor = useWorkflowEditorStore.getState()
    editor.pushHistory()
    editor.setNodes(proposed.nodes || [])
    editor.setEdges((proposed.edges || []).map(e => ({ ...e, type: e.type || 'custom' })))
    set({ active: false, proposed: null, summary: null })
  },

  reject: () => set({ active: false, proposed: null, summary: null }),
}))
