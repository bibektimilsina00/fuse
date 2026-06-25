import React from 'react'
import * as LucideIcons from 'lucide-react'
import { BrandIcon } from './BrandIcon'

import airtable from '@thesvg/icons/airtable'
import discord from '@thesvg/icons/discord'
import facebook from '@thesvg/icons/facebook'
import github from '@thesvg/icons/github'
import gmail from '@thesvg/icons/gmail'
import google from '@thesvg/icons/google'
import googleAnalytics from '@thesvg/icons/google-analytics'
import googleCalendar from '@thesvg/icons/google-calendar'
import googleChat from '@thesvg/icons/google-chat'
import googleCloud from '@thesvg/icons/google-cloud'
import googleCloudStorage from '@thesvg/icons/google-cloud-storage'
import googleDocs from '@thesvg/icons/google-docs'
import googleDrive from '@thesvg/icons/google-drive'
import googleForms from '@thesvg/icons/google-forms'
import googleSearchConsole from '@thesvg/icons/google-search-console'
import googleSheets from '@thesvg/icons/google-sheets'
import googleSlides from '@thesvg/icons/google-slides'
import googleTasks from '@thesvg/icons/google-tasks'
import hubspot from '@thesvg/icons/hubspot'
import instagram from '@thesvg/icons/instagram'
import jira from '@thesvg/icons/jira'
import linear from '@thesvg/icons/linear'
import meta from '@thesvg/icons/meta'
import mongodb from '@thesvg/icons/mongodb'
import mysql from '@thesvg/icons/mysql'
import neo4j from '@thesvg/icons/neo4j'
import notion from '@thesvg/icons/notion'
import openai from '@thesvg/icons/openai'
import perplexity from '@thesvg/icons/perplexity'
import postgresql from '@thesvg/icons/postgresql'
import salesforce from '@thesvg/icons/salesforce'
import slack from '@thesvg/icons/slack'
import stripe from '@thesvg/icons/stripe'
import telegram from '@thesvg/icons/telegram'
import whatsapp from '@thesvg/icons/whatsapp'
import youtube from '@thesvg/icons/youtube'

/**
 * Brand icon registry. Tree-shaken per-import so the bundle only
 * carries the integrations we actually ship — each entry is ~1-3KB of
 * raw SVG string from `@thesvg/icons`. Adding a new integration is one
 * import + one entry in `BRAND_REGISTRY`.
 *
 * Keys cover every spelling the backend has historically used:
 *   - kebab-case slug (`youtube`, `google-sheets`)
 *   - react-icons style (`SiYoutube`, `SiGooglesheets`)
 *   - bare brand name (`Slack`, `Facebook`)
 * That way no node metadata has to change to pick up the new icons.
 */
interface IconModule {
  variants: Record<string, string>
}

const BRAND_REGISTRY: Record<string, IconModule> = {}

function register(slug: string, module: IconModule, ...aliases: string[]) {
  BRAND_REGISTRY[slug.toLowerCase()] = module
  for (const alias of aliases) {
    BRAND_REGISTRY[alias.toLowerCase()] = module
  }
}

register('airtable', airtable, 'SiAirtable')
register('discord', discord, 'SiDiscord')
register('facebook', facebook, 'SiFacebook', 'Facebook')
register('github', github, 'SiGithub')
register('gmail', gmail, 'SiGmail')
register('google', google, 'SiGoogle')
register('google-analytics', googleAnalytics, 'SiGoogleanalytics', 'googleanalytics')
register('google-calendar', googleCalendar, 'SiGooglecalendar', 'googlecalendar')
register('google-chat', googleChat, 'SiGooglechat', 'googlechat')
register('google-cloud', googleCloud, 'SiGooglecloud', 'googlecloud')
register('google-cloud-storage', googleCloudStorage, 'SiGooglecloudstorage', 'googlecloudstorage')
// Google Contacts isn't in theSVG yet — alias to the generic Google mark.
register('google-contacts', google, 'SiGooglecontacts', 'googlecontacts')
register('google-docs', googleDocs, 'SiGoogledocs', 'googledocs')
register('google-drive', googleDrive, 'SiGoogledrive', 'googledrive')
register('google-forms', googleForms, 'SiGoogleforms', 'googleforms')
register('google-search-console', googleSearchConsole, 'SiGooglesearchconsole', 'googlesearchconsole')
register('google-sheets', googleSheets, 'SiGooglesheets', 'googlesheets')
register('google-slides', googleSlides, 'SiGoogleslides', 'googleslides')
register('google-tasks', googleTasks, 'SiGoogletasks', 'googletasks')
register('hubspot', hubspot, 'SiHubspot')
register('instagram', instagram, 'SiInstagram', 'Instagram')
register('jira', jira, 'SiJira')
register('linear', linear, 'SiLinear')
register('meta', meta, 'SiMeta', 'Meta')
register('mongodb', mongodb, 'SiMongodb')
register('mysql', mysql, 'SiMysql')
register('neo4j', neo4j, 'SiNeo4j', 'SiNeo')
register('notion', notion, 'SiNotion')
register('openai', openai, 'SiOpenai')
register('perplexity', perplexity, 'SiPerplexity')
register('postgresql', postgresql, 'SiPostgresql')
register('salesforce', salesforce, 'SiSalesforce')
register('slack', slack, 'SiSlack', 'Slack')
register('stripe', stripe, 'SiStripe')
register('telegram', telegram, 'SiTelegram')
register('whatsapp', whatsapp, 'SiWhatsapp', 'Whatsapp')
register('youtube', youtube, 'SiYoutube')

/**
 * Three-tier icon resolver:
 *
 * 1. **Brand registry** — every theSVG entry above. Matches both the
 *    canonical kebab slug and the legacy `si:Si<Brand>` / bare-name
 *    forms backend metadata still ships. Renders the `mono` variant
 *    (single-color silhouette) so the parent's `text-*` colour can
 *    drive the silhouette on a brand-coloured tile. Falls back to
 *    `default` (full-color) for icons that don't ship a mono variant
 *    (e.g. Slack — its identity is the 4-color logo).
 * 2. **Lucide** — bundled UI icons (`Play`, `Clock`, `Database`, …).
 * 3. **Globe** — last-resort fallback so the node card always renders
 *    something rather than an empty box.
 */
export const getIcon = (iconName: string): React.ReactNode => {
  const brand = resolveBrand(iconName)
  if (brand) {
    return <BrandIcon module={brand} />
  }
  const LucideComponent = (LucideIcons as unknown as Record<string, React.ElementType | undefined>)[iconName]
  if (LucideComponent) {
    return <LucideComponent />
  }
  return <LucideIcons.Globe />
}

function resolveBrand(name: string): IconModule | null {
  const direct = BRAND_REGISTRY[name.toLowerCase()]
  if (direct) return direct
  // Strip the `si:` prefix the backend uses on Iconify-style names so
  // `si:SiYoutube` and `youtube` both resolve from the same map.
  if (name.includes(':')) {
    const tail = name.slice(name.indexOf(':') + 1).toLowerCase()
    return BRAND_REGISTRY[tail] ?? null
  }
  return null
}
