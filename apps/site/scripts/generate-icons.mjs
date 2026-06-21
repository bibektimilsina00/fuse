#!/usr/bin/env node
/**
 * Generate PNG icon variants + OG image from the brand SVG.
 *
 * Run from repo root:
 *   pnpm --filter runmycrew-site exec node scripts/generate-icons.mjs
 *
 * Outputs into apps/site/public/:
 *   - favicon-16x16.png
 *   - favicon-32x32.png
 *   - apple-touch-icon.png         (180x180, iOS home screen)
 *   - icon-192.png                 (PWA manifest)
 *   - icon-512.png                 (PWA manifest, maskable)
 *   - og-default.png               (1200x630, Open Graph + Twitter card)
 *
 * Source of truth: apps/site/public/favicon.svg.
 * Re-run any time the brand mark changes.
 */
import sharp from 'sharp'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const PUBLIC = join(HERE, '..', 'public')

const BG = '#08090a'
const BRAND_PURPLE = '#5e6ad2'
const TEXT_PRIMARY = '#edeef0'
const TEXT_MUTED = '#8a8f98'

// Slimmed inline of public/favicon.svg so we don't depend on disk order.
const FAVICON_SVG = (size) => `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="${size}" height="${size}">
  <rect width="32" height="32" rx="7" fill="${BG}"/>
  <rect x="4"  y="4"  width="17" height="17" rx="6" fill="${BRAND_PURPLE}" opacity="0.45"/>
  <rect x="11" y="11" width="17" height="17" rx="6" fill="${BRAND_PURPLE}"/>
</svg>`.trim()

// Maskable variant — adds safe-area padding so the glyph survives
// Android's circle / squircle / teardrop masking.
const MASKABLE_SVG = (size) => `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="${size}" height="${size}">
  <rect width="32" height="32" fill="${BG}"/>
  <g transform="translate(2 2) scale(0.875)">
    <rect x="4"  y="4"  width="17" height="17" rx="6" fill="${BRAND_PURPLE}" opacity="0.45"/>
    <rect x="11" y="11" width="17" height="17" rx="6" fill="${BRAND_PURPLE}"/>
  </g>
</svg>`.trim()

// Open Graph card — 1200x630. Brand mark on the left, headline + tagline
// stacked on the right. Stays under Twitter's 1MB cap easily.
const OG_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"  stop-color="#0c0d0f"/>
      <stop offset="100%" stop-color="${BG}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.18" cy="0.42" r="0.55">
      <stop offset="0%"  stop-color="${BRAND_PURPLE}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="${BRAND_PURPLE}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect width="1200" height="630" fill="url(#glow)"/>

  <!-- Brand mark, centered vertically, 140px tall -->
  <g transform="translate(120 245)">
    <rect x="0"  y="0"  width="74" height="74" rx="26" fill="${BRAND_PURPLE}" opacity="0.45"/>
    <rect x="32" y="32" width="74" height="74" rx="26" fill="${BRAND_PURPLE}"/>
  </g>

  <!-- Wordmark + tagline -->
  <text x="280" y="284"
        font-family="Inter, system-ui, -apple-system, sans-serif"
        font-size="78" font-weight="600"
        letter-spacing="-2"
        fill="${TEXT_PRIMARY}">RunMyCrew</text>
  <text x="280" y="334"
        font-family="Inter, system-ui, -apple-system, sans-serif"
        font-size="30" font-weight="500"
        fill="${TEXT_MUTED}">Build workflows in plain English.</text>

  <!-- Bottom-rule + URL -->
  <line x1="120" y1="540" x2="1080" y2="540" stroke="${TEXT_MUTED}" stroke-opacity="0.18"/>
  <text x="120" y="585"
        font-family="JetBrains Mono, ui-monospace, monospace"
        font-size="22" font-weight="500"
        fill="${TEXT_MUTED}">runmycrew.com</text>
  <text x="1080" y="585" text-anchor="end"
        font-family="JetBrains Mono, ui-monospace, monospace"
        font-size="22" font-weight="500"
        fill="${TEXT_MUTED}">Crew AI · 80+ integrations · self-hostable</text>
</svg>`.trim()

const targets = [
  { name: 'favicon-16x16.png',     svg: FAVICON_SVG(64),    resize: 16   },
  { name: 'favicon-32x32.png',     svg: FAVICON_SVG(128),   resize: 32   },
  { name: 'apple-touch-icon.png',  svg: FAVICON_SVG(360),   resize: 180  },
  { name: 'icon-192.png',          svg: MASKABLE_SVG(384),  resize: 192  },
  { name: 'icon-512.png',          svg: MASKABLE_SVG(1024), resize: 512  },
  // Meta App Dashboard requires 1024×1024 PNG for the app icon.
  { name: 'icon-1024.png',         svg: FAVICON_SVG(2048),  resize: 1024 },
  // OG card stays JPEG — gradient backgrounds compress poorly as PNG,
  // and every social network accepts JPEG up to 5MB. We render at 2x
  // (2400x1260) for crispness then output as 1200x630.
  { name: 'og-default.jpg',        svg: OG_SVG,             resize: 1200, height: 630, format: 'jpeg' },
]

await mkdir(PUBLIC, { recursive: true })

for (const t of targets) {
  const buf = Buffer.from(t.svg)
  let pipeline = sharp(buf, { density: 384 })

  if (t.resize) {
    pipeline = pipeline.resize(t.resize, t.height ?? t.resize, { fit: 'contain' })
  }

  if (t.format === 'jpeg') {
    pipeline = pipeline.jpeg({ quality: 85, mozjpeg: true, chromaSubsampling: '4:4:4' })
  } else {
    pipeline = pipeline.png({ compressionLevel: 9, effort: 10 })
  }

  await pipeline.toFile(join(PUBLIC, t.name))
  console.log(`  ✓ ${t.name}`)
}

console.log('\nAll icon variants written to apps/site/public/.')
