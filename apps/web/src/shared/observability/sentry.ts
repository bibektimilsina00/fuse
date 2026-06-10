import * as Sentry from '@sentry/react'

/**
 * Initialize Sentry — error capture + session replay + user-feedback widget.
 *
 * No-op when `VITE_SENTRY_DSN` is unset so local dev / unconfigured builds
 * skip the SDK entirely (no noisy console, no network attempts).
 */
export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn || typeof dsn !== 'string') return

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    release: import.meta.env.VITE_RELEASE,
    sendDefaultPii: false,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        // Masks user input / sensitive DOM by default — flip to false only
        // when you've audited what gets recorded.
        maskAllText: true,
        blockAllMedia: true,
      }),
      Sentry.feedbackIntegration({
        autoInject: false,
        colorScheme: 'system',
        showBranding: false,
      }),
    ],
    // Sample 10 % of transactions in prod, all in dev.
    tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
    // Always capture the last 5 s of a session containing an error.
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 1.0,
  })
}
