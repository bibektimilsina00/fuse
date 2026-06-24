import {
  Sparkles,
  CheckCircle2,
  Download,
  Calendar,
  Plug,
  FileDown,
  User as UserIcon,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { TemplateDetail } from '../types/templatesTypes'

/**
 * Right-rail sidebar — Vercel template marketplace's "Installs / Categories
 * / Type / Resources" stack but using the project's tokens. Sticks below
 * the sub-header on lg+; stacks below the main column on smaller widths.
 *
 * Section ordering is intentional: Pricing leads (the most important
 * decision the visitor makes), Creator next (provenance), then the
 * marketing metadata blocks, then quick-action resources.
 */

interface DetailSidebarProps {
  template: TemplateDetail
  missingCredentials: string[]
}

export function DetailSidebar({ template, missingCredentials }: DetailSidebarProps) {
  const navigate = useNavigate()

  return (
    <aside className="flex flex-col gap-[14px] lg:sticky lg:top-[80px]">
      <Block>
        <BlockTitle icon={<Sparkles className="h-3.5 w-3.5" />}>Pricing</BlockTitle>
        {template.is_premium ? (
          <div className="flex items-baseline gap-1">
            <span className="font-mono text-[22px] font-semibold text-[var(--text)] tracking-[-0.02em]">
              {formatPrice(template.price_cents)}
            </span>
            <span className="text-[11.5px] text-[var(--text-faint)] uppercase font-semibold tracking-[0.06em]">
              one-time
            </span>
          </div>
        ) : (
          <div className="flex items-baseline gap-1">
            <span className="font-mono text-[22px] font-semibold text-[var(--ok)] tracking-[-0.02em]">
              Free
            </span>
            <span className="text-[11.5px] text-[var(--text-faint)] uppercase font-semibold tracking-[0.06em]">
              install
            </span>
          </div>
        )}
      </Block>

      {!template.is_official && template.creator && (
        <Block>
          <BlockTitle icon={<UserIcon className="h-3.5 w-3.5" />}>Creator</BlockTitle>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-[8px] bg-[var(--accent)] text-[14px] font-semibold text-white">
              {template.creator.avatar_url ? (
                <img
                  src={template.creator.avatar_url}
                  alt={template.creator.full_name ?? ''}
                  className="h-full w-full object-cover"
                />
              ) : (
                (template.creator.full_name ?? template.creator.email ?? '?')
                  .trim()
                  .charAt(0)
                  .toUpperCase()
              )}
            </div>
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-[13px] font-semibold text-[var(--text)]">
                {template.creator.full_name?.trim() ||
                  template.creator.email?.split('@')[0] ||
                  'Anonymous'}
              </span>
              <span className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-[var(--text-faint)]">
                Published {formatDate(template.created_at)}
              </span>
            </div>
          </div>
        </Block>
      )}

      <Block>
        <BlockTitle icon={<Download className="h-3.5 w-3.5" />}>Installs</BlockTitle>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[22px] font-semibold text-[var(--text)] tracking-[-0.02em]">
            {template.download_count.toLocaleString()}
          </span>
          {template.download_count >= 50 && (
            <span className="flex h-[7px] w-[7px] rounded-full bg-[var(--ok)] animate-[rmcPulse_2.4s_ease-in-out_infinite]" />
          )}
        </div>
      </Block>

      <Block>
        <BlockTitle>Categories</BlockTitle>
        <div className="flex flex-wrap gap-1.5">
          <Pill>{humanCategory(template.category)}</Pill>
          <Pill>{template.kind}</Pill>
        </div>
      </Block>

      <Block>
        <BlockTitle>Type</BlockTitle>
        <div className="flex items-center gap-2 text-[13px] text-[var(--text)]">
          {template.is_official ? (
            <>
              <CheckCircle2 className="h-3.5 w-3.5 text-[var(--accent)]" />
              <span className="font-medium">Official template</span>
            </>
          ) : (
            <>
              <UserIcon className="h-3.5 w-3.5 text-[var(--text-mute)]" />
              <span className="font-medium">Community</span>
            </>
          )}
        </div>
      </Block>

      <Block>
        <BlockTitle icon={<Calendar className="h-3.5 w-3.5" />}>Updated</BlockTitle>
        <span className="font-mono text-[12px] uppercase tracking-[0.06em] text-[var(--text-mute)]">
          {formatDate(template.updated_at)}
        </span>
      </Block>

      <Block>
        <BlockTitle>Resources</BlockTitle>
        <div className="flex flex-col gap-1">
          {missingCredentials.length > 0 && (
            <ResourceLink onClick={() => navigate(APP_ROUTES.CONNECTIONS)}>
              <Plug className="h-3.5 w-3.5 text-[var(--warn)]" />
              Connect {missingCredentials.length} required integration
              {missingCredentials.length === 1 ? '' : 's'}
            </ResourceLink>
          )}
          <ResourceLink onClick={exportJson(template.slug, template.graph)}>
            <FileDown className="h-3.5 w-3.5 text-[var(--text-mute)]" />
            Export workflow JSON
          </ResourceLink>
        </div>
      </Block>
    </aside>
  )
}

// ── Building blocks ──────────────────────────────────────────────

function Block({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] p-[14px]">
      {children}
    </div>
  )
}

function BlockTitle({
  icon,
  children,
}: {
  icon?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <span className="flex items-center gap-1.5 text-[10.5px] font-bold uppercase tracking-[0.08em] text-[var(--text-dim)]">
      {icon}
      {children}
    </span>
  )
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-[6px] border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-mute)]">
      {children}
    </span>
  )
}

function ResourceLink({
  onClick,
  children,
}: {
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-[6px] px-1 py-1.5 text-left text-[12.5px] text-[var(--text-mute)] transition-colors hover:bg-[var(--bg)] hover:text-[var(--text)]"
    >
      {children}
    </button>
  )
}

// ── Helpers ──────────────────────────────────────────────────────

function exportJson(slug: string, graph: Record<string, unknown>) {
  return () => {
    const blob = new Blob([JSON.stringify(graph, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${slug}.workflow.json`
    a.click()
    URL.revokeObjectURL(url)
  }
}

function formatPrice(cents: number): string {
  if (cents <= 0) return 'Free'
  const dollars = cents / 100
  return Number.isInteger(dollars) ? `$${dollars}` : `$${dollars.toFixed(2)}`
}

function humanCategory(cat: string): string {
  return cat
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
