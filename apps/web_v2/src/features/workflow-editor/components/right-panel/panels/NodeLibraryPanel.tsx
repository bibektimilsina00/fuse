import { useState, useMemo } from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import { getIcon } from '../../../utils/icon-map'

const CATEGORY_ORDER = ['trigger', 'action', 'ai', 'logic', 'browser', 'integration'] as const
const CATEGORY_LABEL: Record<string, string> = {
  trigger: 'Triggers', action: 'Actions', ai: 'AI', logic: 'Logic', browser: 'Browser', integration: 'Integrations',
}

export function NodeLibraryPanel() {
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    return q ? nodeDefinitions.filter(d => d.name.toLowerCase().includes(q) || d.description.toLowerCase().includes(q)) : nodeDefinitions
  }, [nodeDefinitions, query])

  const grouped = useMemo(() => {
    const map = new Map<string, typeof filtered>()
    for (const def of filtered) {
      const list = map.get(def.category) ?? []
      list.push(def)
      map.set(def.category, list)
    }
    return CATEGORY_ORDER.filter(c => map.has(c)).map(c => ({ category: c, defs: map.get(c)! }))
  }, [filtered])

  return (
    <div className="flex h-full flex-col">
      {/* Search */}
      <div className="shrink-0 border-b border-[var(--border-faint)] p-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-faint)]" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search nodes…"
            className={cn(
              'h-8 w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]',
              'pl-8 pr-3 text-[12.5px] text-[var(--text)] placeholder:text-[var(--text-dim)]',
              'outline-none transition-colors focus:border-[var(--border-soft)] focus:bg-[var(--bg-2)]',
            )}
          />
        </div>
      </div>

      {/* List */}
      <div className="min-h-0 flex-1 overflow-y-auto p-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {grouped.length === 0 ? (
          <p className="py-8 text-center text-[12px] text-[var(--text-faint)]">No nodes found</p>
        ) : (
          grouped.map(({ category, defs }) => (
            <div key={category} className="mb-3">
              <p className="mb-1 px-2 text-[10.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)]">
                {CATEGORY_LABEL[category] ?? category}
              </p>
              {defs.map(def => {
                const Icon = getIcon(def.icon)
                return (
                  <div
                    key={def.type}
                    draggable
                    onDragStart={e => e.dataTransfer.setData('application/reactflow', def.type)}
                    className={cn(
                      'flex cursor-grab items-center gap-2.5 rounded-[8px] px-2.5 py-2',
                      'transition-colors hover:bg-[var(--surface)] active:cursor-grabbing',
                    )}
                    title={def.description}
                  >
                    <div
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] text-white [&_svg]:h-3 [&_svg]:w-3"
                      style={{ background: def.color ?? 'var(--surface-3)' }}
                    >
                      {Icon}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-[12.5px] font-medium text-[var(--text)]">{def.name}</p>
                      <p className="truncate text-[10.5px] text-[var(--text-faint)]">{def.description}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
