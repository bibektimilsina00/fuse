import { Icons } from '@/shared/components/icons'
import { CardContainer, CardBody, CardItem } from '@/components/ui/aceternity/card-container'
import type { Template, TemplateCreator } from '../types/templatesTypes'
import { CreatorChip } from './CreatorChip'
import { PremiumBadge } from './PremiumBadge'

interface Props {
  template: Template
  // Marketplace extras — optional so older call sites keep working.
  isOfficial?: boolean
  isPremium?: boolean
  priceCents?: number
  creator?: TemplateCreator | null
  downloadCount?: number
  onClick?: () => void
}

export function TemplateCard({
  template,
  isOfficial,
  isPremium,
  priceCents = 0,
  creator,
  downloadCount,
  onClick,
}: Props) {
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
              <div className="inspo-mock">
                <div className="bar" />
                <div className="body-mock" />
              </div>
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
          </CardItem>
        </button>
      </CardBody>
    </CardContainer>
  )
}
