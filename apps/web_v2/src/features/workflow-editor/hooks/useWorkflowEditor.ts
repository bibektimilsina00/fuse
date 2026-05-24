import { useEffect, useCallback, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNodesState, useEdgesState } from 'reactflow'
import type { ApiNodeDefinition, NodeDefinition } from '../types/editorTypes'

import { editorAPI } from '../services/editorAPI'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'

const AUTOSAVE_DELAY = 1500 // ms

function normalizeDefinition(d: ApiNodeDefinition): NodeDefinition {
  return {
    ...d,
    allowError: d.allow_error,
    outputsSchema: d.outputs_schema,
    credentialType: (d.credential_type as string | undefined) ?? undefined,
  }
}

export function useWorkflowEditor(workflowId: string) {
  const storeWorkflow = useWorkflowEditorStore(s => s.workflow)
  const saveState = useWorkflowEditorStore(s => s.saveState)
  const setWorkflow = useWorkflowEditorStore(s => s.setWorkflow)
  const setNodeDefinitions = useWorkflowEditorStore(s => s.setNodeDefinitions)
  const setStoreNodes = useWorkflowEditorStore(s => s.setNodes)
  const setStoreEdges = useWorkflowEditorStore(s => s.setEdges)
  const setSaveState = useWorkflowEditorStore(s => s.setSaveState)
  const setVersionVector = useWorkflowEditorStore(s => s.setVersionVector)
  const setSelectedNodeId = useWorkflowEditorStore(s => s.setSelectedNodeId)
  const setInspectorOpen = useWorkflowEditorStore(s => s.setInspectorOpen)
  const resetEditorStore = useWorkflowEditorStore(s => s.reset)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Fetch node definitions (shared, long-lived cache) ─────────────────────
  const { data: rawDefinitions } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10, // 10 min
  })

  useEffect(() => {
    if (rawDefinitions && rawDefinitions.length > 0) {
      setNodeDefinitions(rawDefinitions.map(normalizeDefinition))
    }
  }, [rawDefinitions, setNodeDefinitions])

  // ── Fetch workflow ────────────────────────────────────────────────────────
  const { data: workflow, isLoading, error } = useQuery({
    queryKey: ['workflow-editor', workflowId],
    queryFn: ({ signal }) => editorAPI.getWorkflow(workflowId, signal),
    staleTime: Infinity, // editor owns the data
  })

  // ── ReactFlow state ───────────────────────────────────────────────────────
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Populate graph when workflow loads
  useEffect(() => {
    if (!workflow) return
    setWorkflow(workflow)
    setVersionVector(workflow.version_vector ?? 0)

    const graph = workflow.graph ?? { nodes: [], edges: [] }
    setNodes(graph.nodes ?? [])
    setEdges(graph.edges ?? [])
    setStoreNodes(graph.nodes ?? [])
    setStoreEdges(graph.edges ?? [])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflow?.id])

  // ── Auto-save ─────────────────────────────────────────────────────────────
  const saveMutation = useMutation({
    mutationFn: ({ graph, version }: { graph: object; version: number }) =>
      editorAPI.saveGraph(workflowId, graph, version),
    onMutate: () => setSaveState('saving'),
    onSuccess: (updated) => {
      setSaveState('saved')
      setVersionVector(updated.version_vector ?? 0)
    },
    onError: () => setSaveState('error'),
  })

  const triggerSave = useCallback((newNodes: typeof nodes, newEdges: typeof edges) => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    setSaveState('unsaved')
    saveTimer.current = setTimeout(() => {
      saveMutation.mutate({
        graph: { nodes: newNodes, edges: newEdges },
        version: useWorkflowEditorStore.getState().versionVector,
      })
    }, AUTOSAVE_DELAY)
  }, [saveMutation, setSaveState])

  const handleNodesChange = useCallback((changes: Parameters<typeof onNodesChange>[0]) => {
    onNodesChange(changes)
  }, [onNodesChange])

  const handleEdgesChange = useCallback((changes: Parameters<typeof onEdgesChange>[0]) => {
    onEdgesChange(changes)
  }, [onEdgesChange])

  // Trigger save on graph changes
  useEffect(() => {
    if (!workflow) return
    setStoreNodes(nodes)
    setStoreEdges(edges)
    triggerSave(nodes, edges)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges])

  const updateNodeData = useCallback((nodeId: string, data: Record<string, unknown>) => {
    setNodes(currentNodes =>
      currentNodes.map(node =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node,
      ),
    )
  }, [setNodes])

  const selectNode = useCallback((nodeId: string | null) => {
    const current = useWorkflowEditorStore.getState()
    const nextOpen = Boolean(nodeId)
    if (current.selectedNodeId !== nodeId) setSelectedNodeId(nodeId)
    if (current.inspectorOpen !== nextOpen) setInspectorOpen(nextOpen)
  }, [setInspectorOpen, setSelectedNodeId])

  // ── Run ───────────────────────────────────────────────────────────────────
  const runMutation = useMutation({
    mutationFn: () => editorAPI.run(workflowId),
  })

  // ── Rename ────────────────────────────────────────────────────────────────
  const renameMutation = useMutation({
    mutationFn: (name: string) => editorAPI.rename(workflowId, name),
    onSuccess: (updated) => setWorkflow(updated),
  })

  // ── Toggle active ─────────────────────────────────────────────────────────
  const toggleMutation = useMutation({
    mutationFn: () => editorAPI.toggleActive(workflowId),
    onSuccess: (res) => {
      if (storeWorkflow) setWorkflow({ ...storeWorkflow, is_active: res.is_active })
    },
  })

  // Cleanup on unmount
  useEffect(() => () => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    resetEditorStore()
  }, [resetEditorStore])

  return {
    workflow,
    isLoading,
    error,
    // Graph
    nodes,
    edges,
    onNodesChange: handleNodesChange,
    onEdgesChange: handleEdgesChange,
    setNodes,
    setEdges,
    updateNodeData,
    selectNode,
    // Actions
    run: runMutation.mutate,
    rename: renameMutation.mutate,
    toggle: toggleMutation.mutate,
    isRunning: runMutation.isPending,
    saveState,
  }
}
