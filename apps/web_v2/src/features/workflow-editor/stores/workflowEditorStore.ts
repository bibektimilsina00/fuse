import { create } from 'zustand'
import type { Node, Edge } from 'reactflow'
import type { SaveState, WorkflowDetail } from '../types/editorTypes'

interface WorkflowEditorState {
  // Loaded workflow meta
  workflow: WorkflowDetail | null
  setWorkflow: (w: WorkflowDetail) => void

  // ReactFlow graph state
  nodes: Node[]
  edges: Edge[]
  setNodes: (nodes: Node[]) => void
  setEdges: (edges: Edge[]) => void
  onNodesChange: ((changes: unknown[]) => void) | null
  onEdgesChange: ((changes: unknown[]) => void) | null

  // Save state
  saveState: SaveState
  setSaveState: (s: SaveState) => void
  versionVector: number
  setVersionVector: (v: number) => void

  // UI state
  selectedNodeId: string | null
  setSelectedNodeId: (id: string | null) => void
  inspectorOpen: boolean
  setInspectorOpen: (open: boolean) => void

  // Reset when leaving editor
  reset: () => void
}

export const useWorkflowEditorStore = create<WorkflowEditorState>((set) => ({
  workflow: null,
  setWorkflow: (workflow) => set({ workflow }),

  nodes: [],
  edges: [],
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  onNodesChange: null,
  onEdgesChange: null,

  saveState: 'saved',
  setSaveState: (saveState) => set({ saveState }),
  versionVector: 0,
  setVersionVector: (versionVector) => set({ versionVector }),

  selectedNodeId: null,
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  inspectorOpen: false,
  setInspectorOpen: (inspectorOpen) => set({ inspectorOpen }),

  reset: () => set({
    workflow: null,
    nodes: [],
    edges: [],
    saveState: 'saved',
    versionVector: 0,
    selectedNodeId: null,
    inspectorOpen: false,
  }),
}))
