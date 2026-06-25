import { useEffect, useState } from 'react'

/**
 * Backing CDN — every theSVG asset lives at
 * `https://thesvg.org/icons/<slug>/<variant>.svg`. Using the CDN
 * directly (not the `@thesvg/icons` npm package) means:
 *
 * - the editor's JS bundle stays lean (no 18MB of static imports);
 * - adding a new integration node requires zero frontend changes —
 *   the backend names a slug, the browser hits the CDN URL;
 * - new icons that theSVG ships after our last deploy become
 *   available instantly, no `pnpm install` required.
 *
 * The cost is one CDN round-trip per icon per session — every
 * subsequent paint hits the browser HTTP cache + the in-memory
 * `iconCache` below.
 */
const CDN_BASE = 'https://thesvg.org/icons'

/** Resolved SVG strings keyed by slug. `null` is cached too, so a
 *  404 doesn't keep banging on the CDN. */
const iconCache = new Map<string, string | null>()

/** In-flight requests keyed by slug. Multiple `<BrandIcon>` mounts
 *  for the same brand share one fetch instead of stampeding the CDN. */
const inflight = new Map<string, Promise<string | null>>()

async function fetchSvg(slug: string): Promise<string | null> {
  if (iconCache.has(slug)) return iconCache.get(slug) ?? null
  const existing = inflight.get(slug)
  if (existing) return existing
  const promise = (async () => {
    // Mono first — what the design wants on a brand-coloured tile.
    // Fall back to default (full-color) when the brand ships no mono
    // variant (theSVG omits one for Slack, whose identity is the
    // four-colour cluster). 404 on both is cached as `null`.
    for (const variant of ['mono', 'default']) {
      try {
        const res = await fetch(`${CDN_BASE}/${slug}/${variant}.svg`)
        if (res.ok) {
          const text = await res.text()
          iconCache.set(slug, text)
          return text
        }
      } catch {
        // Network error — drop through to the next variant / null.
      }
    }
    iconCache.set(slug, null)
    return null
  })()
  inflight.set(slug, promise)
  promise.finally(() => inflight.delete(slug))
  return promise
}

/**
 * Renders a brand mark from theSVG by slug. Paints synchronously on a
 * cache hit; renders a transparent placeholder of the same size while
 * the CDN responds on a cold slug, so the node card never reflows.
 *
 * Lives in its own file so vite-react-refresh stays happy — the
 * surrounding resolver in `icon-map.tsx` is plain data.
 */
export function BrandIcon({ slug }: { slug: string }) {
  const [svg, setSvg] = useState<string | null>(() => iconCache.get(slug) ?? null)

  useEffect(() => {
    let cancelled = false
    void fetchSvg(slug).then((result) => {
      if (!cancelled) setSvg(result)
    })
    return () => {
      cancelled = true
    }
  }, [slug])

  if (!svg) {
    return <span className="inline-block h-full w-full" />
  }
  return (
    <span
      className="inline-flex h-full w-full items-center justify-center [&>svg]:h-full [&>svg]:w-full [&>svg]:fill-current"
      dangerouslySetInnerHTML={{ __html: injectCurrentColor(svg) }}
    />
  )
}

/** Add `fill="currentColor"` to the `<svg>` root when no explicit fill
 *  is set so paths without their own fill inherit the parent colour
 *  instead of falling back to black. Idempotent.
 */
function injectCurrentColor(svg: string): string {
  if (!svg) return svg
  if (/<svg[^>]*\bfill=/i.test(svg)) return svg
  return svg.replace(/<svg(\s)/i, '<svg fill="currentColor"$1')
}
