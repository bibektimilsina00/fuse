import { useEffect, useRef } from 'react'
import * as Sentry from '@sentry/react'

type FeedbackForm = Awaited<ReturnType<NonNullable<ReturnType<typeof Sentry.getFeedback>>['createForm']>>

/**
 * Global keyboard shortcut that opens Sentry's user-feedback dialog.
 *
 * Default binding: ⌘⇧B (mac) / Ctrl+Shift+B (linux/windows). Pass `match` to
 * override (e.g. ⌘I).
 *
 * No-op when the Sentry SDK didn't initialize (DSN unset). Pressing the
 * shortcut while a dialog is already open closes it — toggle behavior.
 */
export function useReportBugShortcut(
  match: (e: KeyboardEvent) => boolean = defaultMatch,
): void {
  const openFormRef = useRef<FeedbackForm | null>(null)

  useEffect(() => {
    const onKeyDown = async (e: KeyboardEvent) => {
      if (!match(e)) return
      e.preventDefault()

      // Toggle: if a form is already attached, tear it down.
      if (openFormRef.current) {
        openFormRef.current.removeFromDom()
        openFormRef.current = null
        return
      }

      const feedback = Sentry.getFeedback()
      if (!feedback) return

      const form = await feedback.createForm()
      form.appendToDom()
      form.open()
      openFormRef.current = form
    }

    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      openFormRef.current?.removeFromDom()
      openFormRef.current = null
    }
  }, [match])
}

function defaultMatch(e: KeyboardEvent): boolean {
  // ⌘⇧B on macOS, Ctrl+Shift+B elsewhere.
  return (e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'b'
}
