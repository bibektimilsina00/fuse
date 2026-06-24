/**
 * Template marketplace types.
 *
 * The original `Template` interface stays compatible with TemplateCard
 * (idx, label, title, kind, steps, bg) so the card visual doesn't need
 * to change — we map the API response into that shape inside the page.
 */

export interface TemplateCreator {
  id: string | null
  full_name: string | null
  email: string | null
  avatar_url: string | null
}

export interface TemplateListItem {
  id: string
  slug: string
  title: string
  summary: string
  category: string
  kind: string
  bg_variant: string
  is_official: boolean
  is_premium: boolean
  price_cents: number
  download_count: number
  steps: number
  featured: boolean
  creator: TemplateCreator | null
  tools_required: string[]
  created_at: string
  updated_at: string
}

export interface TemplateDetail extends TemplateListItem {
  description: string
  graph: Record<string, unknown>
  credentials_required: string[]
  tools_required: string[]
}

export interface TemplateListResponse {
  items: TemplateListItem[]
  total: number
  limit: number
  offset: number
}

export interface TemplateCategory {
  id: string
  label: string
  count: number
}

export interface TemplateCategoryListResponse {
  categories: TemplateCategory[]
}

export interface InstallTemplateResponse {
  workflow_id: string
  message: string
}

// Legacy shape — kept for TemplateCard backward compatibility. The page
// maps a TemplateListItem into this shape before rendering the card.
export interface Template {
  idx: string
  label: string
  title: string
  kind: string
  steps: number
  bg: string
}

export interface PublishTemplateInput {
  workflow_id: string
  title: string
  summary?: string
  description?: string
  category: string
  kind?: string
  bg_variant?: string
  is_premium?: boolean
  price_cents?: number
}

export interface UpdateTemplateInput {
  title?: string
  summary?: string
  description?: string
  category?: string
  kind?: string
  bg_variant?: string
  is_published?: boolean
  is_premium?: boolean
  price_cents?: number
}

export type TemplateSort = 'newest' | 'popular' | 'price-low' | 'price-high'

export const TEMPLATE_CATEGORIES: { id: string; label: string }[] = [
  { id: 'revenue-ops', label: 'Revenue ops' },
  { id: 'engineering', label: 'Engineering' },
  { id: 'inbox', label: 'Inbox' },
  { id: 'reporting', label: 'Reporting' },
  { id: 'sales', label: 'Sales' },
  { id: 'loops', label: 'Loops' },
]

export const TEMPLATE_KINDS: { id: string; label: string }[] = [
  { id: 'flow', label: 'Flow' },
  { id: 'agent', label: 'Agent' },
  { id: 'schedule', label: 'Schedule' },
]

export const TEMPLATE_BG_VARIANTS = [
  'inspo-bg-1',
  'inspo-bg-2',
  'inspo-bg-3',
] as const
