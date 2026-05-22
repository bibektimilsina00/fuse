import { useCallback } from 'react'
import ReactFlow, {
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
} from 'reactflow'
import 'reactflow/dist/style.css'

interface Props {
  nodes: Node[]
  edges: Edge[]
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect?: OnConnect
}

function Flow({ nodes, edges, onNodesChange, onEdgesChange, onConnect }: Props) {
  const handleConnect: OnConnect = useCallback(
    (connection) => {
      if (onConnect) onConnect(connection)
    },
    [onConnect]
  )

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={handleConnect}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.1}
      maxZoom={2}
      defaultEdgeOptions={{ type: 'smoothstep', animated: false }}
      proOptions={{ hideAttribution: true }}
      style={{ background: 'var(--bg)' }}
    >
      {/* Dot grid background matching the app design */}
      <Background
        variant={BackgroundVariant.Dots}
        gap={24}
        size={1}
        color="oklch(0.32 0.004 250)"
        style={{ background: 'var(--bg)' }}
      />

      {/* Controls */}
      <Controls
        style={{
          background: 'var(--bg-2)',
          border: '1px solid var(--border-faint)',
          borderRadius: 10,
        }}
      />

      {/* MiniMap */}
      <MiniMap
        style={{
          background: 'var(--bg-2)',
          border: '1px solid var(--border-faint)',
          borderRadius: 10,
        }}
        maskColor="oklch(0.195 0.003 250 / 0.7)"
        nodeColor="var(--surface-3)"
      />

      {/* Empty state overlay */}
      {nodes.length === 0 && (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center gap-3 pointer-events-none"
          style={{ zIndex: 4 }}
        >
          <div className="w-[48px] h-[48px] rounded-[12px] bg-[var(--surface)] border border-[var(--border-faint)] flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" strokeWidth="1.5">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-[13.5px] font-medium text-[var(--text-mute)]">Empty canvas</p>
            <p className="text-[12px] text-[var(--text-faint)] mt-0.5">
              Add nodes from the panel to build your workflow
            </p>
          </div>
        </div>
      )}
    </ReactFlow>
  )
}

export function EditorCanvas(props: Props) {
  return (
    <ReactFlowProvider>
      <div className="flex-1 min-h-0 min-w-0 relative">
        <Flow {...props} />
      </div>
    </ReactFlowProvider>
  )
}
