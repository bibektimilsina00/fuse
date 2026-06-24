import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Search, Users } from 'lucide-react'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates, useTemplateCategories } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import type {
  Template,
  TemplateListItem,
  TemplateSort,
} from '../types/templatesTypes'

/**
 * Marketplace listing page.
 *
 * Layout chrome mirrors the dashboard — same max-width, same paddings,
 * same eyebrow + h1 type scale — so the templates page reads as part of
 * the product instead of a one-off page.
 */

const SORT_OPTIONS: { id: TemplateSort; label: string }[] = [
  { id: 'newest', label: 'Newest' },
  { id: 'popular', label: 'Most installed' },
  { id: 'price-low', label: 'Price · low → high' },
  { id: 'price-high', label: 'Price · high → low' },
]

export function Templates() {
  const navigate = useNavigate()
  const [cat, setCat] = useState<string>('all')
  const [sort, setSort] = useState<TemplateSort>('newest')
  const [search, setSearch] = useState('')

  const params = useMemo(
    () => ({
      category: cat === 'all' ? undefined : cat,
      sort,
      q: search.trim() || undefined,
      limit: 36,
      offset: 0,
    }),
    [cat, sort, search],
  )

  const { data, isLoading } = useTemplates(params)
  const { data: categoriesData } = useTemplateCategories()

  const categories = categoriesData?.categories ?? []
  const items = data?.items ?? []

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[1160px] mx-auto px-[28px] sm:px-[48px] pt-[40px] sm:pt-[56px] pb-[80px] flex flex-col gap-[32px]">
        {/* Header — matches dashboard's GreetingRow visual rhythm */}
        <div className="flex flex-col gap-[18px]">
          <div className="flex items-center gap-[8px]">
            <span className="relative inline-flex w-[8px] h-[8px]">
              <span className="absolute inset-0 rounded-full bg-[var(--accent)]" />
            </span>
            <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-faint)]">
              MARKETPLACE
            </span>
            <span className="text-[var(--text-dim)]">·</span>
            <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-dim)]">
              {data?.total ?? 0} TEMPLATES
            </span>
          </div>

          <div className="flex items-end justify-between gap-[16px] flex-wrap">
            <div className="flex flex-col gap-[6px] flex-1 min-w-[280px]">
              <h1 className="m-0 text-[27px] font-semibold tracking-[-0.022em] text-[var(--text)]">
                Templates
              </h1>
              <p className="m-0 text-[13.5px] leading-[1.55] text-[var(--text-mute)] max-w-[560px]">
                Browse community + official workflows. Install one to get a
                ready-made graph in your workspace, or publish your own from any
                workflow you've built.
              </p>
            </div>
            <div className="flex items-center gap-[9px] shrink-0">
              <button
                onClick={() => navigate(APP_ROUTES.MY_TEMPLATES)}
                className="inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[6px] text-[13px] font-medium text-[var(--text)] bg-[rgba(255,255,255,0.02)] border border-[var(--border-soft)] transition-colors hover:bg-[rgba(255,255,255,0.05)] hover:border-[var(--border)]"
              >
                <Users className="h-[15px] w-[15px]" /> My templates
              </button>
            </div>
          </div>
        </div>

        {/* Filter / search row — uses the project's standard .filter-bar /
            .filter-tabs vocabulary so the templates page matches the rest
            of the product. */}
        <div className="filter-bar">
          <div className="filter-tabs">
            <button
              className={`filter-tab${cat === 'all' ? ' active' : ''}`}
              onClick={() => setCat('all')}
            >
              All <span className="filter-count">{data?.total ?? 0}</span>
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                className={`filter-tab${cat === c.id ? ' active' : ''}`}
                onClick={() => setCat(c.id)}
              >
                {c.label} <span className="filter-count">{c.count}</span>
              </button>
            ))}
          </div>
          <div className="filter-tools">
            <div className="cmd-search inline-search">
              <Search className="h-3.5 w-3.5" />
              <input
                placeholder="Search templates"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select
              className="h-[30px] rounded-[7px] border border-[var(--border-faint)] bg-[var(--bg-2)] px-2.5 text-[12px] text-[var(--text)] outline-none transition-colors hover:border-[var(--border-soft)] focus:border-[var(--border)]"
              value={sort}
              onChange={(e) => setSort(e.target.value as TemplateSort)}
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Body */}
        {isLoading ? (
          <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading templates…
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-1.5 py-16 text-center text-[var(--text-faint)]">
            <span className="text-[14px] font-semibold text-[var(--text)]">
              No templates yet
            </span>
            <span className="text-[12px]">
              Publish one from a workflow to seed this gallery.
            </span>
          </div>
        ) : (
          <div className="tpl-grid">
            {items.map((item, idx) => (
              <TemplateCard
                key={item.id}
                template={toCardShape(item, idx)}
                isOfficial={item.is_official}
                isPremium={item.is_premium}
                priceCents={item.price_cents}
                creator={item.creator}
                downloadCount={item.download_count}
                toolsRequired={item.tools_required}
                onClick={() => navigate(APP_ROUTES.TEMPLATE_DETAIL(item.slug))}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function toCardShape(item: TemplateListItem, idx: number): Template {
  return {
    idx: String(idx + 1).padStart(2, '0'),
    label: humanCategory(item.category),
    title: item.title,
    kind: item.kind,
    steps: item.steps,
    bg: item.bg_variant,
  }
}

function humanCategory(cat: string): string {
  return cat
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}
