/**
 * Single source of truth for site URLs. Mirrors apps/web's
 * `shared/constants/routes.ts` pattern so links stay refactorable.
 *
 * Hostnames resolve from `NEXT_PUBLIC_*` env vars (baked into the
 * Next.js bundle at build time) with a hardcoded fallback so local
 * `pnpm dev` works without a `.env`. Override in CI via Dockerfile
 * `ARG NEXT_PUBLIC_PRODUCT_URL=` when you rebrand or split envs.
 */
export const MARKETING_URL =
  process.env.NEXT_PUBLIC_MARKETING_URL ?? 'https://runmycrew.com'

export const PRODUCT_URL =
  process.env.NEXT_PUBLIC_PRODUCT_URL ?? 'https://app.runmycrew.com'

export const GITHUB_REPO_URL =
  process.env.NEXT_PUBLIC_GITHUB_REPO_URL ??
  'https://github.com/bibektimilsina00/runmycrew'

export const APP_ROUTES = {
  HOME: '/',
  PRICING: '/pricing',
  DOCS: '/docs',
  CHANGELOG: '/changelog',
  CONTACT: '/contact',
} as const

export const EXTERNAL_LINKS = {
  PRODUCT: PRODUCT_URL,
  GITHUB: GITHUB_REPO_URL,
  LOGIN: `${PRODUCT_URL}/login`,
  REGISTER: `${PRODUCT_URL}/register`,
} as const
