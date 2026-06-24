import type { Template, TemplateListItem } from '../types/templatesTypes'

export function toCardShape(item: TemplateListItem, idx: number): Template {
  return {
    idx: String(idx + 1).padStart(2, '0'),
    label: humanCategory(item.category),
    title: item.title,
    kind: item.kind,
    steps: item.steps,
    bg: item.bg_variant,
    graph: item.graph,
    creator: item.creator,
    is_official: item.is_official,
    is_premium: item.is_premium,
    price_cents: item.price_cents,
  }
}

export function humanCategory(cat: string): string {
  return cat
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}
