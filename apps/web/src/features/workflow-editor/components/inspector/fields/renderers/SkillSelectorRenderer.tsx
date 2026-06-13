import { useMemo, useState } from 'react'
import { AlertTriangle, Check, ExternalLink, Loader2, Plus, Search, Sparkles, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useSkills, SkillIconBadge, type SkillMeta } from '@/features/skills'
import type { RendererProps } from '../types'

/**
 * Multi-select picker for agent skills. The saved value is a list of skill
 * ids — the runtime resolves each id to a `(name, description, content)`
 * row when the agent boots (see `agent._resolve_skills`). Storing ids
 * rather than name snapshots lets users rename a skill without breaking
 * every agent that references it.
 */
function toIdArray(value: unknown): string[] {
  if (!value) return []
  if (Array.isArray(value)) return value.map(String)
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed.map(String) : []
    } catch {
      return []
    }
  }
  return []
}

export function SkillSelectorRenderer({ value, onChange }: RendererProps) {
  const selected = useMemo(() => toIdArray(value), [value])
  const selectedSet = useMemo(() => new Set(selected), [selected])
  const [query, setQuery] = useState('')

  const { data: skills = [], isLoading } = useSkills()

  // Stale ids — selected entries whose skill was deleted (or that never
  // existed). Surfaced as a warning row so the user can prune them; the
  // agent runtime ignores unknown ids silently, so leaving them won't
  // break execution, only clutter storage.
  const knownIds = useMemo(() => new Set(skills.map(s => s.id)), [skills])
  const staleIds = useMemo(
    () => (isLoading ? [] : selected.filter(id => !knownIds.has(id))),
    [isLoading, selected, knownIds],
  )

  // Selected pinned to the top so users see what's active without scrolling.
  // Within each section, sort alphabetically — predictable order beats "by
  // updated_at" which moves rows around between renders.
  const ordered = useMemo(() => {
    const q = query.trim().toLowerCase()
    const filtered = q
      ? skills.filter(s =>
          s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q),
        )
      : skills
    const sorted = [...filtered].sort((a, b) => a.name.localeCompare(b.name))
    return [
      ...sorted.filter(s => selectedSet.has(s.id)),
      ...sorted.filter(s => !selectedSet.has(s.id)),
    ]
  }, [skills, query, selectedSet])

  const toggle = (id: string) => {
    onChange(selectedSet.has(id) ? selected.filter(s => s !== id) : [...selected, id])
  }

  const clearAll = () => onChange([])

  const pruneStale = () => {
    if (!staleIds.length) return
    onChange(selected.filter(id => knownIds.has(id)))
  }

  if (isLoading) {
    return (
      <div className="flex h-9 items-center gap-2 text-[12px] text-text-faint">
        <Loader2 size={13} className="animate-spin" /> Loading skills…
      </div>
    )
  }

  if (skills.length === 0) {
    return (
      <div className="flex flex-col items-start gap-2 rounded-[8px] border border-dashed border-border-faint bg-bg p-4">
        <div className="flex items-center gap-2 text-[12px] text-text-mute">
          <Sparkles size={13} className="text-text-faint" />
          No skills yet.
        </div>
        <p className="text-[11px] text-text-faint">
          Skills are reusable markdown bodies an agent can load on demand instead of
          carrying them in every prompt.
        </p>
        <a
          href={APP_ROUTES.SKILL_NEW}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-[6px] border border-border-faint bg-bg-2 px-2.5 py-1 text-[11.5px] text-text hover:bg-surface"
        >
          <Plus size={12} />
          Create your first skill
          <ExternalLink size={10} className="text-text-faint" />
        </a>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Toolbar — search + selected count + clear */}
      <div className="flex items-center gap-2">
        <div className="flex h-8 flex-1 items-center gap-1.5 rounded-[7px] border border-border-faint bg-bg px-2.5 focus-within:border-border">
          <Search size={12} className="shrink-0 text-text-faint" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Filter…"
            className="min-w-0 flex-1 bg-transparent text-[12px] text-text outline-none placeholder:text-text-faint"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              aria-label="Clear filter"
              className="text-text-faint hover:text-text"
            >
              <X size={11} />
            </button>
          )}
        </div>
        {selected.length > 0 && (
          <button
            type="button"
            onClick={clearAll}
            className="rounded-[6px] border border-border-faint bg-bg px-2 py-1 text-[10.5px] text-text-mute hover:text-text"
            aria-label="Clear all selected skills"
          >
            Clear ({selected.length})
          </button>
        )}
      </div>

      {/* Stale-skill warning — only shown when selected ids point at
          deleted skills. PR5 will extend this to detect content drift too. */}
      {staleIds.length > 0 && (
        <div className="flex items-start gap-2 rounded-[7px] border border-warn/30 bg-warn/10 px-2.5 py-1.5 text-[11px] text-warn">
          <AlertTriangle size={12} className="mt-0.5 shrink-0" />
          <div className="flex-1">
            {staleIds.length} selected {staleIds.length === 1 ? 'skill no longer exists' : 'skills no longer exist'}.
          </div>
          <button
            type="button"
            onClick={pruneStale}
            className="rounded-[5px] border border-warn/40 bg-bg px-1.5 py-0.5 text-[10.5px] text-warn hover:bg-surface"
          >
            Remove
          </button>
        </div>
      )}

      {/* List */}
      {ordered.length === 0 ? (
        <p className="rounded-[7px] border border-dashed border-border-faint bg-bg p-3 text-center text-[11.5px] text-text-faint">
          No skills match &ldquo;{query}&rdquo;.
        </p>
      ) : (
        <div className="flex max-h-[280px] flex-col gap-1 overflow-y-auto pr-0.5">
          {ordered.map(skill => (
            <SkillRow
              key={skill.id}
              skill={skill}
              active={selectedSet.has(skill.id)}
              onToggle={toggle}
            />
          ))}
        </div>
      )}

      {/* Footer actions */}
      <div className="flex items-center justify-between gap-2 border-t border-border-faint pt-2 text-[11px]">
        <a
          href={APP_ROUTES.SKILL_NEW}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-text-mute hover:text-text"
        >
          <Plus size={11} />
          New skill
          <ExternalLink size={9} className="text-text-faint" />
        </a>
        <a
          href={APP_ROUTES.SKILLS}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-text-faint hover:text-text-mute"
        >
          Manage all
          <ExternalLink size={9} />
        </a>
      </div>
    </div>
  )
}

interface SkillRowProps {
  skill: SkillMeta
  active: boolean
  onToggle: (id: string) => void
}

function SkillRow({ skill, active, onToggle }: SkillRowProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(skill.id)}
      className={cn(
        'group flex items-center gap-2.5 rounded-[7px] border px-2 py-1.5 text-left transition-colors',
        active
          ? 'border-[var(--accent-line)]/40 bg-[var(--accent-line)]/10'
          : 'border-border-faint bg-bg hover:bg-surface',
      )}
      aria-pressed={active}
    >
      <SkillIconBadge iconName={skill.icon} color={skill.color} size="sm" />
      <div className="min-w-0 flex-1">
        <div className="truncate text-[12px] font-medium text-text">{skill.name}</div>
        {skill.description ? (
          <div className="truncate text-[10.5px] text-text-faint">{skill.description}</div>
        ) : (
          <div className="text-[10.5px] italic text-text-faint">No description</div>
        )}
      </div>
      <div
        className={cn(
          'flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border transition-colors',
          active ? 'border-[var(--accent)] bg-[var(--accent)] text-bg' : 'border-border-faint',
        )}
      >
        {active && <Check size={10} />}
      </div>
    </button>
  )
}
