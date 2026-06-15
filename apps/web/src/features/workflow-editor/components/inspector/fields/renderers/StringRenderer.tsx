import type { RendererProps } from '../types'
import { ExpressionEditor } from '../expression/ExpressionEditor'

/**
 * Single text field for string properties. Mixed plain-text + embedded
 * `{{ expression }}` blocks live in one editor — completions, syntax
 * highlighting, and ghost preview all activate when the caret enters a
 * `{{ … }}` region, and stand down for free text.
 *
 * Legacy `=expression` saves are transparently migrated to
 * `{{ expression }}` by `ExpressionEditor` on first edit. The backend
 * resolver keeps a silent fallback for any old graph that hasn't been
 * touched since the migration.
 */
export function StringRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const str = value === undefined || value === null ? '' : String(value)
  const opts = prop.typeOptions ?? {}
  // Accept `multiline` / `rows` either at the top of the prop (the shape
  // the Python node definitions actually emit) or nested under
  // `typeOptions` (the shape the editor-side TypeScript type predicts).
  // Both shapes get normalised here so a body field renders as a real
  // textarea instead of a single-line `<input>` with a wrapping overlay.
  const topLevel = prop as { multiline?: unknown; rows?: unknown }
  const multiline = Boolean(opts.multiline ?? topLevel.multiline)
  const rawRows = opts.rows ?? topLevel.rows
  const rows = typeof rawRows === 'number' ? rawRows : multiline ? 6 : 1

  return (
    <ExpressionEditor
      value={str}
      onChange={onChange}
      placeholder={prop.placeholder}
      multiline={multiline}
      rows={rows}
      disabled={disabled}
    />
  )
}
