import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates, useTemplateCategories } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import type {
  Template,
  TemplateListItem,
  TemplateSort,
} from '../types/templatesTypes'

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
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Marketplace · {data?.total ?? 0} templates</span>
          <h1>Templates</h1>
        </div>
        <div className="btn-group">
          <button
            className="btn btn-secondary"
            onClick={() => navigate(APP_ROUTES.MY_TEMPLATES)}
          >
            <Icons.Users /> My templates
          </button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          <button
            className={`filter-tab${cat === 'all' ? ' active' : ''}`}
            onClick={() => setCat('all')}
          >
            All
            <span className="filter-count">{data?.total ?? 0}</span>
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              className={`filter-tab${cat === c.id ? ' active' : ''}`}
              onClick={() => setCat(c.id)}
            >
              {c.label}
              <span className="filter-count">{c.count}</span>
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
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

      {isLoading ? (
        <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
          <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
          Loading templates…
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-1.5 py-16 text-center text-[var(--text-faint)]">
          <span className="text-[13.5px] font-semibold text-[var(--text)]">
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
              onClick={() => navigate(APP_ROUTES.TEMPLATE_DETAIL(item.slug))}
            />
          ))}
        </div>
      )}
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
