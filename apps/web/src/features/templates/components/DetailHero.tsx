import type { TemplateDetail } from '../types/templatesTypes'
import { TemplateGraphPreview } from './TemplateGraphPreview'

/**
 * Big preview block at the top of the detail page — Vercel-style hero
 * with the template's gradient background and an enlarged workflow
 * graph render rendered over it.
 *
 * Below the preview: eyebrow + h1 + summary line. The h1 matches the
 * dashboard's `text-[27px] font-semibold tracking-[-0.022em]` so the
 * detail page reads as part of the product, not a one-off page.
 */

interface DetailHeroProps {
  template: TemplateDetail
}

export function DetailHero({ template }: DetailHeroProps) {
  return (
    <div className="flex flex-col gap-[18px]">
      <div className="flex items-center gap-[8px]">
        <span className="relative inline-flex w-[8px] h-[8px]">
          <span className="absolute inset-0 rounded-full bg-[var(--accent)]" />
        </span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-faint)] uppercase">
          {humanCategory(template.category)}
        </span>
        <span className="text-[var(--text-dim)]">·</span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-dim)] uppercase">
          {template.kind}
        </span>
        {template.is_official && (
          <>
            <span className="text-[var(--text-dim)]">·</span>
            <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--accent)] uppercase">
              Official
            </span>
          </>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <h1 className="m-0 text-[27px] font-semibold tracking-[-0.022em] text-[var(--text)]">
          {template.title}
        </h1>
        {template.summary && (
          <p className="m-0 max-w-[640px] text-[14px] leading-[1.55] text-[var(--text-mute)]">
            {template.summary}
          </p>
        )}
      </div>

      {/* 16:9 preview tile — real editor widgets, read-only */}
      <div className="relative aspect-[16/9] w-full overflow-hidden rounded-[12px] border border-[var(--border-faint)] bg-[var(--bg)]">
        {template.graph?.nodes?.length ? (
          <TemplateGraphPreview graph={template.graph} />
        ) : null}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center gap-2 bg-gradient-to-t from-[oklch(0_0_0/0.55)] to-transparent p-4 text-[11px] font-mono uppercase tracking-[0.08em] text-white/85">
          <span>{(template.graph?.nodes?.length ?? template.steps) || 0} nodes</span>
          <span className="opacity-50">·</span>
          <span>{template.graph?.edges?.length ?? 0} connections</span>
        </div>
      </div>
    </div>
  )
}

function humanCategory(cat: string): string {
  return cat
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}
