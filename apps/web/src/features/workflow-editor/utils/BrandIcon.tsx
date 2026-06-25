interface IconModule {
  variants: Record<string, string>
}

/**
 * Renders a theSVG icon module's `mono` variant inline, patched so
 * its silhouette inherits the parent's `text-*` colour via
 * `fill-current`. Falls back to the `default` (full-color) variant
 * when the module ships no mono (e.g. Slack, whose identity is the
 * four-colour cluster).
 *
 * Lives in its own file because vite-react-refresh requires component
 * modules to export components only — the icon registry around this
 * component is plain data and would trip the rule otherwise.
 */
export function BrandIcon({ module }: { module: IconModule }) {
  const raw = module.variants.mono ?? module.variants.default ?? ''
  const svg = injectCurrentColor(raw)
  return (
    <span
      className="inline-flex h-full w-full items-center justify-center [&>svg]:h-full [&>svg]:w-full [&>svg]:fill-current"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}

/** Add `fill="currentColor"` to the `<svg>` root when no explicit fill
 *  is set, so paths without their own fill inherit the parent colour
 *  instead of falling back to black. Idempotent.
 */
function injectCurrentColor(svg: string): string {
  if (!svg) return svg
  if (/<svg[^>]*\bfill=/i.test(svg)) return svg
  return svg.replace(/<svg(\s)/i, '<svg fill="currentColor"$1')
}
