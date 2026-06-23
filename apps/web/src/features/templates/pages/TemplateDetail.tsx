import { useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Download, Loader2, Sparkles } from 'lucide-react'
import { Button } from '@/shared/components'
import { useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useCredentials } from '@/features/connections/hooks/useConnections'
import { useTemplateDetail, useInstallTemplate } from '../hooks/useTemplates'
import { templatesAPI } from '../services/templatesAPI'
import { CreatorChip } from '../components/CreatorChip'
import { PremiumBadge } from '../components/PremiumBadge'
import { MissingCredentialsAlert } from '../components/MissingCredentialsAlert'

/**
 * `/templates/:slugOrId` detail page.
 *
 * Hero strip + Overview / Requirements panels. The template's React Flow
 * graph isn't rendered visually here in MVP — we show a node count and
 * the required-tools / required-credentials chips instead, which is what
 * users actually need to decide whether to install.
 */

export function TemplateDetail() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const { data: template, isLoading, error } = useTemplateDetail(slug)
  const install = useInstallTemplate()
  const { data: credentials = [] } = useCredentials()

  const connectedTypes = useMemo(
    () => new Set(credentials.map((c) => c.type)),
    [credentials],
  )
  const missing = useMemo(() => {
    if (!template) return []
    return (template.credentials_required || []).filter(
      (c) => !connectedTypes.has(c),
    )
  }, [template, connectedTypes])

  if (isLoading) {
    return (
      <div className="view-body flex items-center gap-3 py-12 text-[13px] text-[var(--text-faint)]">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading template…
      </div>
    )
  }

  if (error || !template) {
    return (
      <div className="view-body flex flex-col items-start gap-3 py-12">
        <h1 className="text-[22px] font-semibold">Template not found</h1>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate(APP_ROUTES.TEMPLATES)}
          leftIcon={<ArrowLeft className="h-3.5 w-3.5" />}
        >
          Back to marketplace
        </Button>
      </div>
    )
  }

  const handleInstall = () => {
    install.mutate(template.slug, {
      onSuccess: (res) => {
        toast(`Installed '${template.title}'`, { variant: 'ok' })
        navigate(APP_ROUTES.WORKFLOW(res.workflow_id))
      },
      onError: (err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status
        if (status === 402) {
          toast('Premium template — purchases coming soon', { variant: 'warn' })
        } else {
          toast('Install failed', { variant: 'err' })
        }
      },
    })
  }

  const handlePurchase = async () => {
    try {
      await templatesAPI.purchase(template.slug)
    } catch {
      // 501 expected — show the same stub message either way
    }
    toast('Template purchases are coming soon', { variant: 'warn' })
  }

  const installable = !template.is_premium

  return (
    <div className="view-body">
      <button
        onClick={() => navigate(APP_ROUTES.TEMPLATES)}
        className="mb-5 inline-flex items-center gap-1.5 text-[12px] font-medium text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to marketplace
      </button>

      {/* Hero */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="rounded-[6px] border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-1 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--text-mute)]">
              {humanCategory(template.category)}
            </span>
            <span className="rounded-[6px] border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-1 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--text-mute)]">
              {template.kind}
            </span>
            {template.is_official && (
              <span className="inline-flex items-center gap-1 rounded-[6px] border border-[var(--accent)]/40 bg-[var(--accent)]/10 px-2 py-1 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--accent)]">
                <Sparkles className="h-3 w-3" /> Official
              </span>
            )}
            {template.is_premium && (
              <PremiumBadge priceCents={template.price_cents} variant="detail" />
            )}
          </div>
          <h1 className="m-0 text-[28px] font-semibold tracking-[-0.018em]">
            {template.title}
          </h1>
          {template.summary && (
            <p className="m-0 max-w-[640px] text-[14px] leading-[1.6] text-[var(--text-mute)]">
              {template.summary}
            </p>
          )}
          <div className="flex items-center gap-4 text-[11.5px] text-[var(--text-faint)]">
            <span>{template.steps} steps</span>
            <span>·</span>
            <span>{template.download_count} installs</span>
            <span>·</span>
            <span>Updated {formatDate(template.updated_at)}</span>
          </div>
          {!template.is_official && template.creator && (
            <CreatorChip creator={template.creator} variant="detail" />
          )}
        </div>

        {/* Side panel */}
        <aside className="flex flex-col gap-3 rounded-[12px] border border-[var(--border-faint)] bg-[var(--bg-2)] p-4">
          <MissingCredentialsAlert missing={missing} />
          {installable ? (
            <Button
              variant="primary"
              onClick={handleInstall}
              disabled={install.isPending}
              loading={install.isPending}
              leftIcon={<Download className="h-3.5 w-3.5" />}
              className="w-full font-semibold"
            >
              {install.isPending ? 'Installing…' : 'Install template'}
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={handlePurchase}
              leftIcon={<Sparkles className="h-3.5 w-3.5" />}
              className="w-full font-semibold"
            >
              Buy for {formatPrice(template.price_cents)}
            </Button>
          )}
          <div className="flex flex-col gap-2 border-t border-[var(--border-faint)] pt-3 text-[11.5px]">
            <Row label="Category" value={humanCategory(template.category)} />
            <Row label="Kind" value={template.kind} />
            <Row label="Steps" value={String(template.steps)} />
            <Row label="Installs" value={String(template.download_count)} />
          </div>
        </aside>
      </div>

      {/* Description */}
      <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
        <section className="flex flex-col gap-3">
          <h2 className="m-0 text-[15px] font-semibold">Overview</h2>
          <div className="prose-docs whitespace-pre-wrap text-[13px] leading-[1.65] text-[var(--text-mute)]">
            {template.description || template.summary || 'No description provided.'}
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <RequirementBlock
            title="Integrations required"
            items={template.credentials_required}
            empty="No integrations required."
          />
          <RequirementBlock
            title="Tools used"
            items={template.tools_required}
            empty="No tools used."
          />
        </section>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[var(--text-faint)]">{label}</span>
      <span className="font-medium text-[var(--text)]">{value}</span>
    </div>
  )
}

function RequirementBlock({
  title,
  items,
  empty,
}: {
  title: string
  items: string[]
  empty: string
}) {
  return (
    <div className="flex flex-col gap-2 rounded-[10px] border border-[var(--border-faint)] bg-[var(--bg-2)] p-4">
      <span className="text-[10.5px] font-bold uppercase tracking-[0.08em] text-[var(--text-dim)]">
        {title}
      </span>
      {items.length === 0 ? (
        <span className="text-[12px] italic text-[var(--text-faint)]">{empty}</span>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {items.map((item) => (
            <span
              key={item}
              className="rounded-[6px] border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-1 font-mono text-[11px] text-[var(--text-mute)]"
            >
              {item}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function humanCategory(cat: string): string {
  return cat
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}

function formatPrice(cents: number): string {
  if (cents <= 0) return 'Free'
  const dollars = cents / 100
  if (Number.isInteger(dollars)) return `$${dollars}`
  return `$${dollars.toFixed(2)}`
}

function formatDate(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
