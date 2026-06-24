import { Icons } from '@/shared/components/icons'
import type { Template } from '../types/templatesTypes'

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
        <div className="index">{template.idx}</div>
        <div className="inspo-mock">
          <div className="bar" />
          <div className="body-mock" />
        </div>
        <div className="label">{template.label}</div>
      </div>
      <div className="inspo-meta">
        <div className="inspo-meta-title">{template.title}</div>
        <div className="inspo-meta-row">
          <span>
            <Icons.Flow /> {template.kind}
          </span>
          <span>{template.steps} steps</span>
        </div>
      </div>
    </button>
  )
}
