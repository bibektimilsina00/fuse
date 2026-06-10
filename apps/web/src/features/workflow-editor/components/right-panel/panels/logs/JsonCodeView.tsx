import React, { useMemo } from 'react'
import EditorImport from 'react-simple-code-editor'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'
import { cn } from '@/lib/cn'

interface EditorProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  onValueChange: (value: string) => void
  highlight: (value: string) => string | React.ReactNode
  padding?: number | { top?: number; right?: number; bottom?: number; left?: number }
  textareaClassName?: string
  preClassName?: string
}

// Defensive CJS interop: depending on Vite's pre-bundle state the default
// import may resolve to the component itself OR to a `{ default: Component }`
// wrapper. Unwrap until we land on something callable as a component.
const Editor = (() => {
  let candidate: unknown = EditorImport
  // Drill at most two levels to avoid an infinite loop on circular shapes.
  for (let i = 0; i < 2; i++) {
    if (typeof candidate === 'function') break
    if (
      candidate &&
      typeof candidate === 'object' &&
      'default' in (candidate as Record<string, unknown>) &&
      (candidate as Record<string, unknown>).default
    ) {
      candidate = (candidate as { default: unknown }).default
      continue
    }
    break
  }
  return candidate as React.ComponentType<EditorProps>
})()

interface Props {
  source: string
  wrap: boolean
}

/**
 * Editor-style read-only JSON viewer.
 *
 * Built on `react-simple-code-editor` for selection + caret + native line
 * navigation, with Prism handling the syntax highlight. We pin `value` to
 * the incoming `source` and keep `onValueChange` a no-op so edits are
 * dropped — the panel is read-only by design.
 *
 * Line numbers are rendered alongside via a side gutter sharing the same
 * line height so the two stay aligned even with text wrap on.
 */
export function JsonCodeView({ source, wrap }: Props) {
  const lineCount = useMemo(() => Math.max(1, source.split('\n').length), [source])
  const gutterDigits = String(lineCount).length

  return (
    <div className="flex h-full min-h-full bg-[var(--bg)] font-mono text-[11.5px] leading-[18px]">
      <Gutter lineCount={lineCount} digits={gutterDigits} />
      <div className="min-w-0 flex-1">
        <Editor
          value={source}
          onValueChange={noop}
          highlight={highlight}
          padding={{ top: 4, right: 12, bottom: 4, left: 12 }}
          textareaClassName="caret-[var(--text)]"
          preClassName={cn(
            'json-code-pre',
            wrap ? 'whitespace-pre-wrap break-words' : 'whitespace-pre',
          )}
          className="json-code-editor"
          style={{
            fontFamily: 'var(--font-mono, ui-monospace, SFMono-Regular, monospace)',
            fontSize: 11.5,
            lineHeight: '18px',
            background: 'transparent',
            color: 'var(--text)',
            minHeight: '100%',
          }}
          // Prevent line-break edits — read-only behavior via swallowed inputs.
          onKeyDown={(e) => {
            // Allow copy / select-all / nav keys; block everything else.
            const isMeta = e.metaKey || e.ctrlKey
            const allow =
              (isMeta && ['c', 'a', 'x'].includes(e.key.toLowerCase())) ||
              ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Home','End','PageUp','PageDown'].includes(e.key) ||
              e.key === 'Tab'
            if (!allow && e.key.length === 1) e.preventDefault()
          }}
        />
      </div>
    </div>
  )
}

function Gutter({ lineCount, digits }: { lineCount: number; digits: number }) {
  const width = digits * 8 + 18
  return (
    <div
      aria-hidden
      className="sticky left-0 z-[1] flex shrink-0 select-none flex-col items-end border-r border-[var(--border-faint)] bg-[var(--bg)] pt-1 pr-2 text-[var(--text-faint)]"
      style={{ width }}
    >
      {Array.from({ length: lineCount }).map((_, i) => (
        <div key={i} className="tabular-nums">
          {i + 1}
        </div>
      ))}
    </div>
  )
}

function highlight(code: string): string {
  return Prism.highlight(code, Prism.languages.json, 'json')
}

function noop() {}
