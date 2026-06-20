import type { Metadata, Viewport } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Analytics } from '@vercel/analytics/next'
import { MARKETING_URL } from '@/shared/constants/routes'
import './globals.css'

const sans = Inter({
  variable: '--font-sans',
  subsets: ['latin'],
  display: 'swap',
})

const mono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
  display: 'swap',
})

// Google Search Console + Meta Domain Verification tokens land here so we
// can verify domain ownership without futzing with DNS round-trips. Override
// at build time with `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION` / `NEXT_PUBLIC_META_DOMAIN_VERIFICATION`
// once the consoles emit the strings.
const GOOGLE_VERIFICATION =
  process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION || undefined
const META_VERIFICATION =
  process.env.NEXT_PUBLIC_META_DOMAIN_VERIFICATION || undefined

export const viewport: Viewport = {
  themeColor: '#08090a',
  width: 'device-width',
  initialScale: 1,
  colorScheme: 'dark',
}

export const metadata: Metadata = {
  title: {
    default: 'RunMyCrew — Build workflows in plain English',
    template: '%s · RunMyCrew',
  },
  description:
    'RunMyCrew is the automation platform that turns natural-language prompts into production workflows. Connect any app, ship in minutes, audit every run.',
  metadataBase: new URL(MARKETING_URL),
  applicationName: 'RunMyCrew',
  authors: [{ name: 'RunMyCrew' }],
  creator: 'RunMyCrew',
  publisher: 'RunMyCrew',
  keywords: [
    'workflow automation',
    'AI agents',
    'no-code',
    'Zapier alternative',
    'open source automation',
    'crew AI',
    'OAuth integrations',
    'self-hosted automation',
  ],
  category: 'productivity',
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    siteName: 'RunMyCrew',
    title: 'RunMyCrew — Build workflows in plain English',
    description:
      'Turn natural-language prompts into production workflows. Connect any app, ship in minutes, audit every run.',
    url: MARKETING_URL,
    locale: 'en_US',
    images: [
      {
        url: '/og-default.png',
        width: 1200,
        height: 630,
        alt: 'RunMyCrew — automation system for teams and agents',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@runmycrew',
    creator: '@runmycrew',
    title: 'RunMyCrew — Build workflows in plain English',
    description:
      'Turn natural-language prompts into production workflows. Connect any app, ship in minutes, audit every run.',
    images: ['/og-default.png'],
  },
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
    ],
    apple: [{ url: '/apple-touch-icon.png', sizes: '180x180' }],
  },
  manifest: '/site.webmanifest',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-snippet': -1,
      'max-image-preview': 'large',
      'max-video-preview': -1,
    },
  },
  verification: {
    google: GOOGLE_VERIFICATION,
    other: META_VERIFICATION ? { 'facebook-domain-verification': [META_VERIFICATION] } : undefined,
  },
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`dark ${sans.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <TooltipProvider delayDuration={200}>{children}</TooltipProvider>
        <Analytics />
      </body>
    </html>
  )
}
