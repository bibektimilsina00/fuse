import { Icons } from '@/shared/components/icons'
import { CardContainer, CardBody, CardItem } from '@/components/ui/aceternity/card-container'
import type { Template } from '../types/templatesTypes'

interface Props {
  template: Template
  onClick?: () => void
}

export function TemplateCard({ template, onClick }: Props) {
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
                <span>{template.steps} steps</span>
              </div>
            </div>
          </CardItem>
        </button>
      </CardBody>
    </CardContainer>
  )
}
