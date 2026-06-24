import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import type { NodeDefinition } from '@/features/workflow-editor/types/editorTypes'
import type { TemplateGraph } from '../types/templatesTypes'

/**
 * Inline mini-render of a template's workflow inside the card art.
 *
 * Renders **actual node tiles** — same look as the editor canvas, just
 * scaled down: rounded coloured square with a Lucide icon plus a small
 * label underneath. Edges drawn as a bezier SVG layer behind the tiles
 * so they read as a smaller version of the real canvas, not an abstract
 * preview.
 *
 * Node icon + colour come from the shared `/nodes/` definitions catalog
 * (same TanStack Query cache key the editor uses, so the fetch happens
 * once across the app).
 */

interface WorkflowMiniPreviewProps {
  graph: TemplateGraph
}

// Card preview canvas. Tuned so the largest seeded loop template (7 nodes)
// fits without overlap while individual tiles stay legible at this size.
const VIEW_W = 100
const VIEW_H = 64
const TILE_W = 22
const TILE_H = 22
const LABEL_GAP = 2
const PADDING = 6

export function WorkflowMiniPreview({ graph }: WorkflowMiniPreviewProps) {
  const { data: definitions = [] } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10,
  })

  const defByType = useMemo(() => {
    const map = new Map<string, NodeDefinition>()
    for (const def of definitions) map.set(def.type, def)
    return map
  }, [definitions])

  const rawNodes = graph?.nodes ?? []
  const rawEdges = graph?.edges ?? []

  const positioned = rawNodes
    .filter((n) => n.position && Number.isFinite(n.position.x) && Number.isFinite(n.position.y))
    .map((n) => ({ ...n, position: n.position! }))

  if (positioned.length === 0) return null

  // Scale the raw editor coords into the small preview viewport.
  const xs = positioned.map((n) => n.position.x)
  const ys = positioned.map((n) => n.position.y)
  const minX = Math.min(...xs)
  const minY = Math.min(...ys)
  const rawW = Math.max(1, Math.max(...xs) - minX)
  const rawH = Math.max(1, Math.max(...ys) - minY)

  const availW = VIEW_W - PADDING * 2 - TILE_W
  const availH = VIEW_H - PADDING * 2 - TILE_H - LABEL_GAP - 6
  const scale = Math.min(availW / rawW, availH / rawH, 0.06)
  const offsetX = PADDING + (availW - rawW * scale) / 2
  const offsetY = PADDING + (availH - rawH * scale) / 2

  const screened = positioned.map((n) => ({
    ...n,
    sx: offsetX + (n.position.x - minX) * scale,
    sy: offsetY + (n.position.y - minY) * scale,
  }))
  const byId = new Map(screened.map((n) => [n.id, n]))

  return (
    <div className="pointer-events-none absolute inset-0">
      {/* SVG edge layer behind the tiles. */}
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0 h-full w-full"
        aria-hidden
      >
        {rawEdges.map((edge, i) => {
          const src = byId.get(edge.source)
          const tgt = byId.get(edge.target)
          if (!src || !tgt) return null
          const x1 = src.sx + TILE_W
          const y1 = src.sy + TILE_H / 2
          const x2 = tgt.sx
          const y2 = tgt.sy + TILE_H / 2
          const handle = Math.max(6, Math.abs(x2 - x1) / 2)
          return (
            <path
              key={edge.id ?? `e-${i}`}
              d={`M ${x1} ${y1} C ${x1 + handle} ${y1}, ${x2 - handle} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke="oklch(0.85 0.01 250 / 0.55)"
              strokeWidth={0.7}
            />
          )
        })}
      </svg>

      {/* Node tiles — positioned divs so Lucide icons render crisp at any
          card size. */}
      <div className="absolute inset-0">
        {screened.map((n) => {
          const def = defByType.get(n.type ?? '')
          const colour = def?.color ?? fallbackColor(n.type)
          const left = (n.sx / VIEW_W) * 100
          const top = (n.sy / VIEW_H) * 100
          const w = (TILE_W / VIEW_W) * 100
          const label = def?.name ?? readableLabel(n.type)
          return (
            <div
              key={n.id}
              className="absolute flex flex-col items-center gap-[1px]"
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${w}%`,
              }}
            >
              <div
                className="flex aspect-square w-full items-center justify-center rounded-[3px] text-white shadow-[0_2px_4px_-2px_oklch(0_0_0/0.4)] [&_svg]:h-[60%] [&_svg]:w-[60%]"
                style={{ background: colour }}
              >
                {def ? getIcon(def.icon) : null}
              </div>
              <span className="max-w-full truncate font-mono text-[5px] uppercase tracking-[0.04em] text-[var(--text)]/85">
                {label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function fallbackColor(type?: string): string {
  if (!type) return 'var(--surface-3)'
  if (type.startsWith('trigger.')) return 'var(--ok)'
  if (type.startsWith('logic.')) return 'var(--warn)'
  if (type.startsWith('ai.') || type === 'action.agent') return '#8b5cf6'
  if (type.startsWith('action.')) return 'var(--accent)'
  return 'var(--surface-3)'
}

function readableLabel(type?: string): string {
  if (!type) return ''
  const parts = type.split('.')
  return parts[parts.length - 1].replace(/_/g, ' ')
}
