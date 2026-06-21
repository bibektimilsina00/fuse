import { ArrowLeft } from 'lucide-react'
import type { ReactNode } from 'react'

interface AuthShellProps {
  /** Center card content — login form / signup form / reset card. */
  children: ReactNode
  /** Where the top-left back arrow goes. Default: marketing site root. */
  backHref?: string
  /** Hover/aria label for the back arrow. */
  backLabel?: string
}

const MARKETING_URL =
  import.meta.env.VITE_MARKETING_URL || 'https://runmycrew.com'

/**
 * Auth pages bypass the user's color-scheme + light/dark choice and lock
 * to the marketing site's dark surface so the handoff from the marketing
 * apex to the app login page is one continuous canvas. Theme variables
 * are overridden inline on the shell, so children that read var(--bg) /
 * var(--text) / var(--accent) etc. all retint inside the scope.
 */
const AUTH_THEME = {
  '--bg':          '#08090a',
  '--bg-2':        '#0c0d0f',
  '--surface':     '#0f1011',
  '--surface-2':   '#161719',
  '--text':        '#edeef0',
  '--text-body':   '#c7c9ce',
  '--text-mute':   '#8a8f98',
  '--text-faint':  '#62666d',
  '--text-dim':    '#52565d',
  '--accent':      '#5e6ad2',
  '--accent-soft': 'rgba(94, 106, 210, 0.14)',
  '--accent-line': 'rgba(94, 106, 210, 0.45)',
  '--border':      'rgba(255, 255, 255, 0.11)',
  '--border-soft': 'rgba(255, 255, 255, 0.07)',
  '--border-faint':'rgba(255, 255, 255, 0.04)',
  // Marketing site stack: Inter + JetBrains Mono with Linear-style
  // OpenType features. Locks auth typography to the site even though
  // the rest of the product uses Inter Tight + Geist Mono.
  '--font-ui':   '"Inter", system-ui, -apple-system, sans-serif',
  '--font-mono': '"JetBrains Mono", ui-monospace, "SF Mono", monospace',
  fontFamily:    '"Inter", system-ui, -apple-system, sans-serif',
  fontFeatureSettings: '"cv01", "ss03"',
  fontVariationSettings: '"opsz" auto',
  textRendering: 'optimizeLegibility',
  WebkitFontSmoothing: 'antialiased',
} as React.CSSProperties

export function AuthShell({
  children,
  backHref = MARKETING_URL,
  backLabel = 'Back to home',
}: AuthShellProps) {
  const isExternal = /^https?:\/\//.test(backHref)
  return (
    <div
      style={AUTH_THEME}
      className="relative flex min-h-screen w-full flex-col bg-[var(--bg)] text-[var(--text)]"
    >
      <header className="mx-auto flex h-16 w-full max-w-[1280px] items-center px-7">
        <a
          href={backHref}
          {...(isExternal ? { rel: 'noopener' } : {})}
          className="inline-flex items-center gap-1.5 text-[13.5px] text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
        >
          <ArrowLeft className="h-[14px] w-[14px]" strokeWidth={1.9} />
          {backLabel}
        </a>
      </header>

      <main className="relative flex flex-1 items-center justify-center px-6 pb-[72px] pt-8">
        <div className="w-full max-w-[392px]">{children}</div>
      </main>
    </div>
  )
}
