/**
 * RunMyCrew brand mark — a four-node graph: one solid lead square plus
 * three satellites at descending opacity. All four rects use
 * `currentColor`, so the mark inherits its accent from its parent —
 * set `text-primary`, `text-foreground`, etc on the wrapper.
 *
 * Pass `drift` to play the 3s satellite-drift loop (used on the hero);
 * leave it off for static surfaces (nav, footer, dashboard mocks).
 */
export function BrandMark({
  className,
  drift = false,
}: {
  className?: string
  drift?: boolean
}) {
  return (
    <svg viewBox="0 0 64 64" fill="none" className={className} aria-hidden>
      <rect x="38" y="24" width="16" height="16" rx="5" fill="currentColor" />
      <rect
        x="19"
        y="11"
        width="13"
        height="13"
        rx="4.5"
        fill="currentColor"
        opacity="0.72"
        style={
          drift
            ? { transformOrigin: '25.5px 17.5px', animation: 'rmcDrift 3s ease-in-out infinite' }
            : undefined
        }
      />
      <rect
        x="19"
        y="40"
        width="13"
        height="13"
        rx="4.5"
        fill="currentColor"
        opacity="0.72"
        style={
          drift
            ? { transformOrigin: '25.5px 46.5px', animation: 'rmcDrift 3s ease-in-out infinite reverse' }
            : undefined
        }
      />
      <rect x="3" y="25.5" width="11" height="11" rx="3.6" fill="currentColor" opacity="0.42" />
    </svg>
  )
}
