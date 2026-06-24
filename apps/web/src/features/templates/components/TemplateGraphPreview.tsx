import { useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactFlow, {
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  type Edge,
  type Node,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { normalizeDefinition } from '@/features/workflow-editor/hooks/useWorkflowEditor'
import { buildNodeTypes } from '@/features/workflow-editor/constants/nodeTypes'
import { CustomEdge } from '@/features/workflow-editor/components/edges/CustomEdge'
import { useWorkflowEditorStore } from '@/features/workflow-editor/stores/workflowEditorStore'
import type { TemplateDetail } from '../types/templatesTypes'

interface Props {
  graph: TemplateDetail['graph']
  /** Static mode: no pan/zoom. Used in card thumbnails. */
  static?: boolean
}

const edgeTypes = { custom: CustomEdge }

function PreviewInner({ graph, static: isStatic = false }: Props) {
  const nodeDefinitions = useWorkflowEditorStore((s) => s.nodeDefinitions)
  const setNodeDefinitions = useWorkflowEditorStore((s) => s.setNodeDefinitions)

  const { data: rawDefinitions } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10,
  })

  useEffect(() => {
    if (rawDefinitions && rawDefinitions.length > 0 && nodeDefinitions.length === 0) {
      setNodeDefinitions(rawDefinitions.map(normalizeDefinition))
    }
  }, [rawDefinitions, nodeDefinitions.length, setNodeDefinitions])

  const nodeTypes = useMemo(() => buildNodeTypes(nodeDefinitions), [nodeDefinitions])

  const nodes: Node[] = useMemo(
    () =>
      (graph?.nodes ?? []).map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position ?? { x: 0, y: 0 },
        data: n.data ?? {},
        draggable: false,
        selectable: false,
        connectable: false,
      })),
    [graph],
  )

  const edges: Edge[] = useMemo(
    () =>
      (graph?.edges ?? []).map((e, i) => ({
        id: e.id ?? `e${i}`,
        source: e.source,
        target: e.target,
        type: 'custom',
        animated: false,
      })),
    [graph],
  )

  if (nodeDefinitions.length === 0) {
    return (
      <div className="absolute inset-0 flex items-center justify-center text-[12px] text-[var(--text-faint)]">
        Loading preview…
      </div>
    )
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      panOnDrag={!isStatic}
      zoomOnScroll={!isStatic}
      zoomOnPinch={!isStatic}
      zoomOnDoubleClick={!isStatic}
      panOnScroll={false}
      preventScrolling={!isStatic}
      fitView
      fitViewOptions={{ padding: isStatic ? 0.1 : 0.2, maxZoom: isStatic ? 0.6 : 1 }}
      minZoom={0.05}
      maxZoom={2}
      proOptions={{ hideAttribution: true }}
      defaultEdgeOptions={{ type: 'custom', animated: false }}
      style={{ background: 'var(--bg)', pointerEvents: isStatic ? 'none' : 'auto' }}
    >
      <Background
        variant={BackgroundVariant.Dots}
        gap={24}
        size={1}
        color="oklch(0.32 0.004 250)"
        style={{ background: 'var(--bg)' }}
      />
    </ReactFlow>
  )
}

export function TemplateGraphPreview({ graph, static: isStatic }: Props) {
  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      <ReactFlowProvider>
        <PreviewInner graph={graph} static={isStatic} />
      </ReactFlowProvider>
    </div>
  )
}
