import { Icons } from '@/shared/components/icons'
import { CardContainer, CardBody, CardItem } from '@/components/ui/aceternity/card-container'
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
 * Original card shell — Aceternity CardContainer + CardBody + CardItem
 * stack — preserved exactly as it was before the marketplace work.
 *
 * Only the inner preview area changes: the static `inspo-mock` striped
 * placeholder is replaced with a real `WorkflowMiniPreview` rendering
 * the template's actual node tiles + edges. Templates that ship without
 * graph data fall back to `TemplatePreview` (tool chips).
 */

interface Props {
  template: Template
  isOfficial?: boolean
  isPremium?: boolean
  priceCents?: number
  creator?: TemplateCreator | null
  downloadCount?: number
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
  const hasGraph = (graph?.nodes?.length ?? 0) > 0
  return (
    <CardContainer containerClassName="w-full">
      <CardBody>
        <button
          type="button"
          onClick={onClick}
          className="inspo-card text-left w-full block"
        >
          <CardItem translateZ={20} className="w-full">
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
          </CardItem>
          <CardItem translateZ={10} className="w-full">
            <div className="inspo-meta">
              <div className="inspo-meta-title">{template.title}</div>
              <div className="inspo-meta-row">
                <span>
                  <Icons.Flow /> {template.kind}
                </span>
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
          </CardItem>
        </button>
      </CardBody>
    </CardContainer>
  )
}
