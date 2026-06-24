import { Crown } from 'lucide-react'

/**
 * Premium badge — gold-tinted overlay sized so it reads as a
 * "paid product" marker, not a generic accent chip. Used on:
 *   - card variant: top-right of `inspo-art`, absolute overlay
 *   - detail variant: inline pill in the detail hero / sidebar
 *
 * Gold tone via raw oklch (not a token) — only used by this badge so
 * it stays distinct from the product's accent everywhere else.
 */

interface PremiumBadgeProps {
  priceCents: number
  variant?: 'card' | 'detail'
}

const GOLD = 'oklch(0.82 0.16 85)'
const GOLD_DEEP = 'oklch(0.68 0.18 75)'

export function PremiumBadge({ priceCents, variant = 'card' }: PremiumBadgeProps) {
  const formatted = formatPrice(priceCents)

  if (variant === 'detail') {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-[8px] px-2.5 py-1 text-[12px] font-semibold text-[oklch(0.18_0.03_85)]"
        style={{
          background: `linear-gradient(135deg, ${GOLD}, ${GOLD_DEEP})`,
        }}
      >
        <Crown className="h-3.5 w-3.5" />
        Premium · {formatted}
      </span>
    )
  }

  return (
    <span
      className="pointer-events-none absolute right-[10px] top-[10px] z-10 inline-flex items-center gap-1.5 rounded-[7px] px-2 py-[3px] text-[10.5px] font-bold uppercase tracking-[0.08em] text-[oklch(0.18_0.03_85)]"
      style={{
        background: `linear-gradient(135deg, ${GOLD}, ${GOLD_DEEP})`,
      }}
    >
      <Crown className="h-3 w-3" />
      {formatted}
    </span>
  )
}

function formatPrice(cents: number): string {
  if (cents <= 0) return 'Free'
  const dollars = cents / 100
  if (Number.isInteger(dollars)) return `$${dollars}`
  return `$${dollars.toFixed(2)}`
}
