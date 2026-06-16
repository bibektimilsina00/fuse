import { useState } from 'react'
import { Search, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useNodeLibrary, CATEGORY_LABEL } from '../../../hooks/useNodeLibrary'
import { getIcon } from '../../../utils/icon-map'

export function NodeLibraryPanel() {
  const { query, setQuery, grouped, spawnNode, onDragStart } = useNodeLibrary()
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({})

  const toggleCategory = (category: string) => {
    setCollapsedCategories(prev => ({
      ...prev,
      [category]: !prev[category],
    }))
  }

  return (
    <div className="flex h-full flex-col bg-[var(--bg-2)]">
      <div className="shrink-0 border-b border-[var(--border-faint)] p-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-faint)]" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search nodes…"
            className={cn(
              'h-8 w-full rounded-md border border-[var(--border-faint)] bg-[var(--surface)]',
              'pl-8 pr-3 text-[12.5px] text-[var(--text)] placeholder:text-[var(--text-dim)]',
              'outline-none transition-colors focus:border-[var(--border-soft)] focus:bg-[var(--bg-2)]',
            )}
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {grouped.length === 0 ? (
          <p className="py-8 text-center text-[12px] text-[var(--text-faint)]">No nodes found</p>
        ) : (
          grouped.map(({ category, defs }) => {
            const isCollapsed = collapsedCategories[category] ?? false
            return (
              <div key={category} className="mb-2">
                <button
                  type="button"
                  onClick={() => toggleCategory(category)}
                  className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left transition-colors hover:bg-[var(--surface)] group"
                >
                  <span className="text-[10.5px] font-semibold uppercase tracking-widest text-[var(--text-mute)] group-hover:text-[var(--text)] transition-colors">
                    {CATEGORY_LABEL[category] ?? category}
                    <span className="ml-1.5 font-mono text-[9px] font-normal text-[var(--text-dim)]">
                      ({defs.length})
                    </span>
                  </span>
                  <ChevronDown
                    className={cn(
                      'h-3.5 w-3.5 text-[var(--text-faint)] transition-transform duration-200 group-hover:text-[var(--text-mute)]',
                      isCollapsed && '-rotate-90',
                    )}
                  />
                </button>
                <div
                  className={cn(
                    'mt-0.5 overflow-hidden transition-all duration-200',
                    isCollapsed ? 'max-h-0 opacity-0' : 'max-h-[1000px] opacity-100',
                  )}
                >
                  {defs.map(def => {
                    const Icon = getIcon(def.icon)
                    return (
                      <div
                        key={def.type}
                        draggable
                        onClick={() => spawnNode(def)}
                        onDragStart={e => onDragStart(e, def)}
                        className={cn(
                          'flex cursor-pointer select-none items-center gap-2.5 rounded-md px-2.5 py-2',
                          'transition-colors hover:bg-[var(--surface)] active:bg-[var(--surface-2)] active:cursor-grabbing',
                        )}
                        title="Click to add · Drag to position"
                      >
                        <div
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm text-white [&_svg]:h-3 [&_svg]:w-3"
                          style={{ background: def.color ?? 'var(--surface-3)' }}
                        >
                          {Icon}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[12.5px] font-medium text-[var(--text)]">{def.name}</p>
                          <p className="truncate text-[10.5px] text-[var(--text-faint)]">{def.description}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

