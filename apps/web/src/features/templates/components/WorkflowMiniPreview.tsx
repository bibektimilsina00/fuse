import type { TemplateGraph } from '../types/templatesTypes'

/**
 * Lightweight SVG render of a workflow graph.
 *
 * Designed to live inside the `.inspo-art` card panel. Reads the
 * template's node positions, normalises them into the SVG's viewBox,
 * draws a bezier edge for each connection, and draws a small rounded
 * tile per node coloured by category. No React Flow — 36 cards on a
 * marketplace grid don't need that many real instances.
 */

interface WorkflowMiniPreviewProps {
  graph: TemplateGraph
}

const VIEWBOX_W = 320
const VIEWBOX_H = 200
const NODE_W = 36
const NODE_H = 20
const PADDING = 18

export function WorkflowMiniPreview({ graph }: WorkflowMiniPreviewProps) {
  const rawNodes = graph?.nodes ?? []
  const rawEdges = graph?.edges ?? []

  // Skip empty / malformed graphs. Caller decides what to show instead.
  const positioned = rawNodes
    .filter((n) => n.position && Number.isFinite(n.position.x) && Number.isFinite(n.position.y))
    .map((n) => ({ ...n, position: n.position! }))

  if (positioned.length === 0) return null

  // Compute the bounding box of the raw positions so we can scale into
  // the viewBox without distorting aspect ratio.
  const xs = positioned.map((n) => n.position.x)
  const ys = positioned.map((n) => n.position.y)
  const minX = Math.min(...xs)
  const minY = Math.min(...ys)
  const rawW = Math.max(1, Math.max(...xs) - minX)
  const rawH = Math.max(1, Math.max(...ys) - minY)

  // Available area inside padding.
  const availW = VIEWBOX_W - PADDING * 2 - NODE_W
  const availH = VIEWBOX_H - PADDING * 2 - NODE_H
  // Single uniform scale so the layout keeps its proportions.
  const scale = Math.min(availW / rawW, availH / rawH)

  // Centre the scaled bounding box inside the available area.
  const scaledW = rawW * scale
  const scaledH = rawH * scale
  const offsetX = PADDING + (availW - scaledW) / 2
  const offsetY = PADDING + (availH - scaledH) / 2

  const toScreen = (x: number, y: number) => ({
    x: offsetX + (x - minX) * scale,
    y: offsetY + (y - minY) * scale,
  })

  const nodesById = new Map(
    positioned.map((n) => {
      const p = toScreen(n.position.x, n.position.y)
      return [n.id, { ...n, screen: p }]
    }),
  )

  return (
    <svg
      viewBox={`0 0 ${VIEWBOX_W} ${VIEWBOX_H}`}
      preserveAspectRatio="xMidYMid meet"
      className="absolute inset-0 h-full w-full"
      aria-hidden
    >
      {/* Faint dot grid backdrop — same vocabulary as the editor canvas. */}
      <defs>
        <pattern id="tpl-dotgrid" width="14" height="14" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="0.7" fill="currentColor" className="text-[var(--text-faint)]" opacity={0.35} />
        </pattern>
      </defs>
      <rect width={VIEWBOX_W} height={VIEWBOX_H} fill="url(#tpl-dotgrid)" />

      {/* Edges first so node tiles sit on top. */}
      {rawEdges.map((edge, i) => {
        const src = nodesById.get(edge.source)
        const tgt = nodesById.get(edge.target)
        if (!src || !tgt) return null
        const x1 = src.screen.x + NODE_W / 2
        const y1 = src.screen.y + NODE_H / 2
        const x2 = tgt.screen.x + NODE_W / 2
        const y2 = tgt.screen.y + NODE_H / 2
        // Bezier with horizontal handles — matches the editor's connector
        // shape so the preview reads as a smaller version of the real thing.
        const handle = Math.max(20, Math.abs(x2 - x1) / 2)
        const path = `M ${x1} ${y1} C ${x1 + handle} ${y1}, ${x2 - handle} ${y2}, ${x2} ${y2}`
        return (
          <path
            key={edge.id ?? `e-${i}`}
            d={path}
            fill="none"
            stroke="var(--border-soft)"
            strokeWidth={1.2}
            opacity={0.85}
          />
        )
      })}

      {/* Nodes */}
      {positioned.map((n) => {
        const p = nodesById.get(n.id)!.screen
        const colour = colourFor(n.type)
        return (
          <g key={n.id} transform={`translate(${p.x}, ${p.y})`}>
            <rect
              width={NODE_W}
              height={NODE_H}
              rx={4}
              fill={colour}
              opacity={0.95}
              stroke="oklch(0 0 0 / 0.25)"
              strokeWidth={0.5}
            />
            {/* Tiny port markers so the node reads as connectable. */}
            <circle cx={0} cy={NODE_H / 2} r={1.6} fill="white" opacity={0.85} />
            <circle cx={NODE_W} cy={NODE_H / 2} r={1.6} fill="white" opacity={0.85} />
          </g>
        )
      })}
    </svg>
  )
}

function colourFor(type?: string): string {
  if (!type) return 'var(--surface-3)'
  if (type.startsWith('trigger.')) return 'var(--ok)'
  if (type.startsWith('logic.')) return 'var(--warn)'
  if (type.startsWith('ai.') || type === 'action.agent') return '#8b5cf6'
  if (type.startsWith('action.')) return 'var(--accent)'
  return 'var(--surface-3)'
}
