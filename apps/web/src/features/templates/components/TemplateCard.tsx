import { Icons } from '@/shared/components/icons'
import type {
  Template,
  TemplateCreator,
  TemplateGraph,
} from '../types/templatesTypes'
import { CreatorChip } from './CreatorChip'
import { PremiumBadge } from './PremiumBadge'
import { TemplatePreview } from './TemplatePreview'
import { WorkflowMiniPreview } from './WorkflowMiniPreview'

/**
 * Plain card (no 3D tilt). The Aceternity CardContainer used to wrap
 * this and rotateX/rotateY on cursor move — felt jittery on a dense
 * grid. The .inspo-card CSS already handles a subtle translateY lift
 * + border-soft brighten on hover; that reads cleaner.
 */

interface Props {
  template: Template
  // Marketplace extras — optional so older call sites keep working.
  isOfficial?: boolean
  isPremium?: boolean
  priceCents?: number
  creator?: TemplateCreator | null
  downloadCount?: number
  // Live preview data — drives the new card-art inset instead of the
  // static inspo-mock striped graphic. `graph` paints a real workflow
  // mini-preview; `toolsRequired` is the fallback chip preview for
  // templates that ship without graph data.
  toolsRequired?: string[]
  graph?: TemplateGraph
  onClick?: () => void
}

export function TemplateCard({
  template,
  isOfficial,
  isPremium,
  priceCents = 0,
  creator,
  downloadCount,
  toolsRequired = [],
  graph,
  onClick,
}: Props) {
  // Real workflow mini-preview wins when the template ships graph data;
  // fall back to the tool-chip preview for legacy / placeholder rows.
  const hasGraph = (graph?.nodes?.length ?? 0) > 0
  return (
    <button
      type="button"
      onClick={onClick}
      className="inspo-card text-left w-full block"
    >
      <div className={`inspo-art ${template.bg}`}>
        <div className="index">{template.idx}</div>
        {isPremium && <PremiumBadge priceCents={priceCents} />}
        {hasGraph ? (
          <WorkflowMiniPreview graph={graph!} />
        ) : (
          <TemplatePreview
            tools={toolsRequired}
            steps={template.steps}
            kind={template.kind}
          />
        )}
        <div className="label">{template.label}</div>
      </div>
      <div className="inspo-meta">
        <div className="inspo-meta-title">{template.title}</div>
        <div className="inspo-meta-row">
          <span>
            <Icons.Flow /> {template.kind}
          </span>
          {/* Creator chip replaces the static "N steps" slot when a
              template was published by a user; official templates keep
              showing the step count so the seeded library reads as
              platform content. */}
          {isOfficial || !creator ? (
            <span>{template.steps} steps</span>
          ) : (
            <CreatorChip creator={creator} />
          )}
          {downloadCount != null && downloadCount > 0 && (
            <span title="Installs">↓ {downloadCount}</span>
          )}
        </div>
      </div>
    </button>
  )
}
