import { Sparkles } from 'lucide-react'

/**
 * Small badge that overlays the top-right of the `inspo-art` panel when
 * a template is paid. Pure absolute-positioned overlay — does not touch
 * the existing card layout / inspo-mock / label.
 *
 * Price is rendered as USD; cents-precision tail (`.99`) only when
 * non-zero so $5 reads "$5" not "$5.00".
 */

interface PremiumBadgeProps {
  priceCents: number
  variant?: 'card' | 'detail'
}

export function PremiumBadge({ priceCents, variant = 'card' }: PremiumBadgeProps) {
  const formatted = formatPrice(priceCents)

  if (variant === 'detail') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-[7px] border border-[var(--accent)]/40 bg-[var(--accent)]/10 px-2 py-1 text-[12px] font-semibold text-[var(--accent)]">
        <Sparkles className="h-3.5 w-3.5" />
        Premium · {formatted}
      </span>
    )
  }

  return (
    <span className="pointer-events-none absolute right-[10px] top-[10px] z-10 inline-flex items-center gap-1 rounded-[6px] bg-[var(--accent)] px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.06em] text-white shadow-[0_4px_12px_-4px_oklch(0_0_0/0.6)]">
      <Sparkles className="h-2.5 w-2.5" />
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
