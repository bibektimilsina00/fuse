import React from 'react'
import { Icon as IconifyIcon } from '@iconify/react'
import * as LucideIcons from 'lucide-react'

/**
 * Three-tier icon resolver, one entry point.
 *
 * 1. **Iconify-prefixed names** (`si:youtube`, `mdi:home`, etc.) go
 *    straight to `@iconify/react` — CDN-loaded, localStorage-cached.
 *    Backend nodes use this for every official integration.
 * 2. **Bare names** are tried against lucide-react first (bundled,
 *    instant). Used for trigger / logic / UI nodes (`Play`, `Clock`,
 *    `Database`).
 * 3. **Bare brand names not in Lucide** (`Slack`, `Facebook`, …)
 *    fall through to Iconify with a `simple-icons:` prefix so they
 *    still resolve as the brand logo instead of the Globe fallback.
 *
 * All Iconify renders use the canonical white-on-brand-bg styling
 * via the `text-current` CSS color, so the SVG inherits whatever
 * color the parent sets. Simple Icons ship paths using `currentColor`,
 * matching how every Lucide icon already paints itself.
 */
export const getIcon = (iconName: string): React.ReactNode => {
  if (iconName.includes(':')) {
    return (
      <IconifyIcon
        icon={normaliseIconifyName(iconName)}
        // Iconify's `color` prop forces `style.color` on the wrapper
        // span; we inherit it from the parent (`text-white` on node
        // headers) so brand-bg + brand-logo always stays legible.
        color="currentColor"
      />
    )
  }
  const LucideComponent = (LucideIcons as unknown as Record<string, React.ElementType | undefined>)[iconName]
  if (LucideComponent) {
    return <LucideComponent />
  }
  // Brand-name fallback: backend metadata still ships bare names like
  // `"Slack"` / `"Facebook"` / `"Instagram"` from before the `si:`
  // convention. Treat any bare name as a Simple Icons slug rather than
  // dumping into the Globe fallback. Iconify simply renders nothing
  // when the slug doesn't exist, which is no worse than today.
  const slug = brandNameToSlug(iconName)
  if (slug) {
    return <IconifyIcon icon={`simple-icons:${slug}`} color="currentColor" />
  }
  return <LucideIcons.Globe />
}

/**
 * Curated map of react-icons-style identifiers → Simple Icons slug.
 * The lossy "lowercase Si<brand>" form backend uses can't be
 * deterministically un-mashed back to kebab — so add new integrations
 * here when they ship.
 */
const SI_BRAND_ALIASES: Record<string, string> = {
  airtable: 'airtable',
  anthropic: 'anthropic',
  discord: 'discord',
  facebook: 'facebook',
  github: 'github',
  gmail: 'gmail',
  google: 'google',
  googleanalytics: 'googleanalytics',
  googlecalendar: 'googlecalendar',
  googlechat: 'googlechat',
  googlecloudstorage: 'googlecloud',
  googlecontacts: 'googlecontacts',
  googledocs: 'googledocs',
  googledrive: 'googledrive',
  googleforms: 'googleforms',
  googlesearchconsole: 'googlesearchconsole',
  googlesheets: 'googlesheets',
  googleslides: 'googleslides',
  googletasks: 'googletasks',
  hubspot: 'hubspot',
  instagram: 'instagram',
  jira: 'jira',
  linear: 'linear',
  linkedin: 'linkedin',
  meta: 'meta',
  mongodb: 'mongodb',
  mysql: 'mysql',
  neo4j: 'neo4j',
  notion: 'notion',
  openai: 'openai',
  perplexity: 'perplexity',
  postgresql: 'postgresql',
  salesforce: 'salesforce',
  slack: 'slack',
  stripe: 'stripe',
  telegram: 'telegram',
  twitter: 'twitter',
  x: 'x',
  youtube: 'youtube',
  whatsapp: 'whatsapp',
  zapier: 'zapier',
}

function brandNameToSlug(name: string): string | null {
  const lowered = name.toLowerCase()
  return SI_BRAND_ALIASES[lowered] ?? null
}

function normaliseIconifyName(raw: string): string {
  const colon = raw.indexOf(':')
  if (colon === -1) return raw
  const prefix = raw.slice(0, colon)
  let tail = raw.slice(colon + 1)
  if (prefix === 'si' && tail.startsWith('Si') && tail.length > 2 && tail[2] === tail[2].toUpperCase()) {
    tail = tail.slice(2)
  }
  const lowered = tail.toLowerCase()
  if (prefix === 'si' && SI_BRAND_ALIASES[lowered]) {
    return `simple-icons:${SI_BRAND_ALIASES[lowered]}`
  }
  const kebab = tail
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1-$2')
    .toLowerCase()
  return `${prefix}:${kebab}`
}
