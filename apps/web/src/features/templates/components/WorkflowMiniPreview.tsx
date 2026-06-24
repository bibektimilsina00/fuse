import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import type { NodeDefinition } from '@/features/workflow-editor/types/editorTypes'
import type { TemplateGraph } from '../types/templatesTypes'

/**
 * Read-only mini render of a workflow graph used on the detail page's
 * hero preview block. Renders node positions normalised into a viewBox,
 * bezier edges, and node tiles coloured by category. Pulls icon + colour
 * from the shared /nodes/ catalog so node visuals match the editor.
 *
 * `density` lets the caller trade tile size against legibility:
 *   - "compact" (default) — hero size, ~140×84 viewBox so seven nodes fit
 *   - "comfortable" — workflow-tab size, ~220×120 with bigger tiles
 */

interface WorkflowMiniPreviewProps {
  graph: TemplateGraph
  density?: 'compact' | 'comfortable'
}

const VIEWPORT = {
  compact: { w: 140, h: 84, tile: 24, padding: 8 },
  comfortable: { w: 220, h: 120, tile: 32, padding: 12 },
} as const

export function WorkflowMiniPreview({
  graph,
  density = 'compact',
}: WorkflowMiniPreviewProps) {
  const { data: definitions = [] } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10,
  })

  const defByType = useMemo(() => {
    const map = new Map<string, NodeDefinition>()
    for (const d of definitions) map.set(d.type, d)
    return map
  }, [definitions])

  const view = VIEWPORT[density]
  const rawNodes = graph?.nodes ?? []
  const rawEdges = graph?.edges ?? []
  const positioned = rawNodes
    .filter((n) => n.position && Number.isFinite(n.position.x) && Number.isFinite(n.position.y))
    .map((n) => ({ ...n, position: n.position! }))

  if (positioned.length === 0) return null

  const xs = positioned.map((n) => n.position.x)
  const ys = positioned.map((n) => n.position.y)
  const minX = Math.min(...xs)
  const minY = Math.min(...ys)
  const rawW = Math.max(1, Math.max(...xs) - minX)
  const rawH = Math.max(1, Math.max(...ys) - minY)

  const availW = view.w - view.padding * 2 - view.tile
  const availH = view.h - view.padding * 2 - view.tile
  const scale = Math.min(availW / rawW, availH / rawH)
  const offsetX = view.padding + (availW - rawW * scale) / 2
  const offsetY = view.padding + (availH - rawH * scale) / 2

  const screened = positioned.map((n) => ({
    ...n,
    sx: offsetX + (n.position.x - minX) * scale,
    sy: offsetY + (n.position.y - minY) * scale,
  }))
  const byId = new Map(screened.map((n) => [n.id, n]))

  return (
    <div className="pointer-events-none absolute inset-0">
      <svg
        viewBox={`0 0 ${view.w} ${view.h}`}
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0 h-full w-full"
        aria-hidden
      >
        {rawEdges.map((edge, i) => {
          const src = byId.get(edge.source)
          const tgt = byId.get(edge.target)
          if (!src || !tgt) return null
          const x1 = src.sx + view.tile
          const y1 = src.sy + view.tile / 2
          const x2 = tgt.sx
          const y2 = tgt.sy + view.tile / 2
          const handle = Math.max(6, Math.abs(x2 - x1) / 2)
          return (
            <path
              key={edge.id ?? `e-${i}`}
              d={`M ${x1} ${y1} C ${x1 + handle} ${y1}, ${x2 - handle} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke="oklch(0.85 0.01 250 / 0.55)"
              strokeWidth={density === 'comfortable' ? 1 : 0.7}
            />
          )
        })}
      </svg>

      <div className="absolute inset-0">
        {screened.map((n) => {
          const def = defByType.get(n.type ?? '')
          const colour = def?.color ?? fallbackColor(n.type)
          const left = (n.sx / view.w) * 100
          const top = (n.sy / view.h) * 100
          const w = (view.tile / view.w) * 100
          const label = def?.name ?? readableLabel(n.type)
          return (
            <div
              key={n.id}
              className="absolute flex flex-col items-center gap-[1px]"
              style={{ left: `${left}%`, top: `${top}%`, width: `${w}%` }}
            >
              <div
                className="flex aspect-square w-full items-center justify-center rounded-[4px] text-white shadow-[0_2px_4px_-2px_oklch(0_0_0/0.45)] [&_svg]:h-[55%] [&_svg]:w-[55%]"
                style={{ background: colour }}
              >
                {def ? getIcon(def.icon) : null}
              </div>
              <span className="max-w-full truncate font-mono text-[6px] uppercase tracking-[0.04em] text-[var(--text)]/85">
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
