import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ReactFlowProvider } from 'reactflow'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowEditor } from '../hooks/useWorkflowEditor'
import { useEditorShortcuts } from '../hooks/useEditorShortcuts'
import { useCopilotDiffStore } from '../stores/copilotDiffStore'
import { useCopilotPendingStore } from '../stores/copilotPendingStore'
import { useEditorLayoutStore } from '../stores/editorLayoutStore'
import { EditorCanvas } from '../components/canvas/EditorCanvas'
import { EditorRightPanel } from '../components/right-panel/EditorRightPanel'
import { BottomPanel } from '../components/bottom-panel/BottomPanel'
import { EditorLoading } from '../components/overlays/EditorLoading'
import { EditorError } from '../components/overlays/EditorError'

export function WorkflowEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  useEditorShortcuts()

  // ── Fullscreen / Zen Mode ────────────────────────────────────────────────
  const [zenMode, setZenMode] = useState(false)

  // Sync browser fullscreen changes (e.g. user presses Esc)
  useEffect(() => {
    const onFsChange = () => {
      setZenMode(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', onFsChange)
    return () => document.removeEventListener('fullscreenchange', onFsChange)
  }, [])

  const toggleZenMode = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }, [])

  // ── Workflow data ────────────────────────────────────────────────────────
  const {
    workflow,
    isLoading,
    error,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    updateNodeData,
    selectNode,
    run,
    isRunning,
  } = useWorkflowEditor(id ?? '')

  const diffActive = useCopilotDiffStore(s => s.active)
  const proposed   = useCopilotDiffStore(s => s.proposed)
  const baseline   = useCopilotDiffStore(s => s.baseline)
  const summary    = useCopilotDiffStore(s => s.summary)

  // ── Copilot preview overlay ───────────────────────────────────────
  //
  // When a Copilot diff is active we keep the user's existing graph as
  // the base layer and OVERLAY the proposed changes on top — edited
  // nodes swap in place (keeping the prior position if the LLM didn't
  // emit one), added nodes append with a deterministic fallback
  // position next to the existing cluster (no more 0,0 stacking),
  // deleted nodes stay as ghosts so the user can see what's about to
  // disappear. Every overlay node carries a `_preview` flag that
  // `WorkflowNode` reads to render dashed-border + accent ring + ghost
  // opacity, signalling "proposed, not yet applied".
  //
  // Preview nodes are individually `draggable:false / selectable:false`
  // so the user can pan + zoom (interactive stays on) without
  // accidentally mutating the proposal — that's also why `interactive`
  // is no longer gated on `diffActive`.
  const canvasNodes = useMemo(() => {
    if (!diffActive || !proposed || !summary || !baseline) return nodes
    const added   = new Set(summary.added)
    const edited  = new Set(summary.edited)
    const deleted = new Set(summary.deleted)
    const propById = new Map(proposed.nodes.map(n => [n.id, n] as const))

    // Fallback layout: drop added nodes that arrived without coords to
    // the right of the existing cluster, stacked vertically.
    const xs = nodes.map(n => n.position?.x ?? 0)
    const ys = nodes.map(n => n.position?.y ?? 0)
    const maxX = xs.length ? Math.max(...xs) : 0
    const avgY = ys.length ? ys.reduce((a, b) => a + b, 0) / ys.length : 0
    let addedIdx = 0
    const positionFor = (n: { position?: { x: number; y: number } }) => {
      const p = n.position
      const hasReal =
        p && Number.isFinite(p.x) && Number.isFinite(p.y) && (p.x !== 0 || p.y !== 0)
      if (hasReal) return p
      const fallback = { x: maxX + 320, y: avgY + addedIdx * 140 }
      addedIdx += 1
      return fallback
    }

    const base = nodes.map(n => {
      if (edited.has(n.id)) {
        const prop = propById.get(n.id)
        return {
          ...n,
          ...(prop ?? {}),
          position: prop?.position ?? n.position,
          data: {
            ...n.data,
            ...(prop?.data ?? {}),
            __diff: 'edited' as const,
            _preview: 'edited' as const,
          },
          draggable: false,
          selectable: false,
        }
      }
      if (deleted.has(n.id)) {
        return {
          ...n,
          draggable: false,
          selectable: false,
          data: { ...n.data, __diff: 'deleted' as const, _preview: 'deleted' as const },
        }
      }
      return n
    })

    const addedNodes = proposed.nodes
      .filter(n => added.has(n.id))
      .map(n => ({
        ...n,
        position: positionFor(n),
        draggable: false,
        selectable: false,
        data: { ...n.data, __diff: 'new' as const, _preview: 'added' as const },
      }))

    return [...base, ...addedNodes]
  }, [diffActive, proposed, baseline, summary, nodes])

  const canvasEdges = useMemo(() => {
    if (!diffActive || !proposed) return edges
    const liveById = new Map(edges.map(e => [e.id, e] as const))
    const propIds  = new Set(proposed.edges.map(e => e.id))
    const merged = proposed.edges.map(e =>
      liveById.get(e.id) ?? {
        ...e,
        type: e.type ?? 'custom',
        animated: true,
        data: { ...e.data, _preview: 'added' as const },
      },
    )
    for (const e of edges) {
      if (!propIds.has(e.id)) merged.push(e)
    }
    return merged
  }, [diffActive, proposed, edges])

  const hasPending = useCopilotPendingStore(s => !!s.prompt)
  useEffect(() => {
    if (hasPending && workflow?.id) {
      useEditorLayoutStore.getState().focusTab('copilot')
    }
  }, [hasPending, workflow?.id])

  if (isLoading) return <EditorLoading />
  if (error || !workflow) return <EditorError onBack={() => navigate(APP_ROUTES.AUTOMATIONS)} />

  return (
    <ReactFlowProvider>
      {/* ── Editor shell ─────────────────────────────────────────────── */}
      <div className="relative flex h-full w-full flex-col overflow-hidden">
        {/* Main content area */}
        <div className="relative flex min-h-0 flex-1 overflow-hidden">
          {/* Canvas + Bottom Panel Column */}
          <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
            {/* Canvas */}
            <div className="relative flex min-h-0 flex-1">
              <EditorCanvas
                nodes={canvasNodes}
                edges={canvasEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onSelectNode={selectNode}
                interactive={true}
                onToggleFullscreen={toggleZenMode}
                isFullscreen={zenMode}
              />
            </div>

            {/* Bottom panel */}
            <BottomPanel
              nodes={nodes}
              updateNodeData={updateNodeData}
              onRun={() => run()}
              isRunning={isRunning}
            />
          </div>

          {/* Right panel (expandable sidebar only — no strip) */}
          <EditorRightPanel
            nodes={nodes}
            updateNodeData={updateNodeData}
            onRun={() => run()}
            isRunning={isRunning}
          />
        </div>
      </div>
    </ReactFlowProvider>
  )
}
