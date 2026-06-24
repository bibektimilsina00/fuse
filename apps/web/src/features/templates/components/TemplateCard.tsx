import { Icons } from '@/shared/components/icons'
import { BadgeCheck } from 'lucide-react'
import type { Template } from '../types/templatesTypes'
import { TemplateGraphPreview } from './TemplateGraphPreview'
import { CreatorChip } from './CreatorChip'
import { PremiumBadge } from './PremiumBadge'

interface Props {
  template: Template
  onClick?: () => void
}

/**
 * No Aceternity 3D tilt — the rotateX/Y mouse-tracking felt jittery on
 * a grid. The card uses a clean CSS hover lift + shadow (see
 * `.inspo-card` in index.css) so motion stays predictable and reads as
 * the same vocabulary as the rest of the product's cards.
 */
export function TemplateCard({ template, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inspo-card text-left w-full block"
    >
      <div className={`inspo-art ${template.bg}`}>
        {template.is_premium && (template.price_cents ?? 0) > 0 ? (
          <PremiumBadge priceCents={template.price_cents ?? 0} />
        ) : (
          <span className="pointer-events-none absolute right-[10px] top-[10px] z-10 inline-flex items-center rounded-[6px] border border-[var(--border-faint)] bg-[var(--bg-2)]/85 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--text-faint)] backdrop-blur-sm">
            Free
          </span>
        )}
        <div className="inspo-mock">
          {template.graph?.nodes?.length ? (
            <TemplateGraphPreview graph={template.graph} static />
          ) : (
            <>
              <div className="bar" />
              <div className="body-mock" />
            </>
          )}
        </div>
        <div className="label">{template.label}</div>
      </div>
      <div className="inspo-meta">
        <div className="inspo-meta-title">{template.title}</div>
        <div className="inspo-meta-row">
          <span>
            <Icons.Flow /> {template.kind}
          </span>
          <span>·</span>
          <span>{template.steps} steps</span>
        </div>
        <div className="mt-1.5 flex items-center gap-2 border-t border-[var(--border-faint)] pt-2">
          {template.is_official ? (
            <span className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-[0.06em] text-[var(--accent)]">
              <BadgeCheck className="h-[12px] w-[12px]" />
              Official
            </span>
          ) : template.creator ? (
            <CreatorChip creator={template.creator} />
          ) : (
            <span className="text-[10px] font-mono uppercase tracking-[0.06em] text-[var(--text-faint)]">
              Community
            </span>
          )}
        </div>
      </div>
    </button>
  )
}
