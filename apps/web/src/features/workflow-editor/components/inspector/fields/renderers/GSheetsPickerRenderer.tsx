import { useEffect, useRef, useState } from 'react'
import { FileSpreadsheet, Loader2, Plus, Search } from 'lucide-react'
import { Button, Input, Modal } from '@/shared/components'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

/**
 * Google Sheets spreadsheet picker — server-proxied list + inline
 * "create new spreadsheet" CTA.
 *
 * Backend endpoints
 *   GET  /credentials/{id}/sheets/spreadsheets?query=...
 *   POST /credentials/{id}/sheets/spreadsheets  body:{title, sheet_titles[]}
 *
 * Stored value
 *   `{ id, name }` — picker can render the picked name back; the runtime
 *   coerces both `{id, name}` and a bare string id via the Pydantic
 *   field validator so legacy graphs keep working.
 */

interface PickerValue {
  id: string
  name: string
}

interface SpreadsheetEntry {
  id: string
  name: string
  modifiedTime?: string
  webViewLink?: string
}

interface SpreadsheetsResponse {
  spreadsheets: SpreadsheetEntry[]
}

interface CreateResponse {
  id: string
  name: string
  webViewLink?: string
}

function parseValue(v: unknown): PickerValue | null {
  if (typeof v === 'string') {
    if (!v) return null
    return { id: v, name: v }
  }
  if (v && typeof v === 'object' && 'id' in v) {
    const obj = v as { id?: string; name?: string }
    if (typeof obj.id === 'string' && obj.id) {
      return { id: obj.id, name: obj.name || obj.id }
    }
  }
  return null
}

export function GSheetsPickerRenderer({
  value,
  onChange,
  disabled,
  properties,
}: RendererProps) {
  const selected = parseValue(value)
  const [open, setOpen] = useState(false)
  const credentialId =
    typeof properties?.credential === 'string' ? properties.credential : ''

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setOpen(true)}
          disabled={disabled || !credentialId}
          title={!credentialId ? 'Pick a Google account on this node first.' : undefined}
          className={cn(
            'inline-flex items-center gap-1.5 h-8 px-3 rounded-[5px] text-xs font-medium',
            'border border-border bg-surface hover:bg-surface-2 text-text transition-colors',
            (disabled || !credentialId) && 'opacity-50 cursor-not-allowed',
          )}
        >
          <FileSpreadsheet className="h-3.5 w-3.5" />
          {selected ? 'Change spreadsheet' : 'Pick spreadsheet'}
        </button>
        {selected && (
          <div className="min-w-0 flex-1 truncate text-xs">
            <span className="font-medium text-text">{selected.name}</span>
            <span className="ml-1.5 font-mono text-[10.5px] text-text-muted">
              {selected.id.slice(0, 10)}…
            </span>
          </div>
        )}
        {selected && (
          <button
            type="button"
            onClick={() => onChange('')}
            disabled={disabled}
            className="text-[11px] text-text-muted hover:text-text"
            title="Clear selection"
          >
            Clear
          </button>
        )}
      </div>

      {open && credentialId && (
        <SpreadsheetBrowser
          credentialId={credentialId}
          onSelect={(picked) => {
            onChange({ id: picked.id, name: picked.name })
            setOpen(false)
          }}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  )
}

// ── modal ────────────────────────────────────────────────────────────────

function SpreadsheetBrowser({
  credentialId,
  onSelect,
  onClose,
}: {
  credentialId: string
  onSelect: (sheet: { id: string; name: string }) => void
  onClose: () => void
}) {
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<SpreadsheetEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Debounce the query to avoid hammering Drive's `files.list` on every
  // keystroke. 250 ms feels responsive while collapsing typing bursts.
  const debouncedQuery = useDebounced(query, 250)

  useEffect(() => {
    let alive = true
    // Showing the spinner + clearing any prior error is the whole
    // point of this effect — eslint's set-state-in-effect rule
    // doesn't fit data-fetching effects.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    apiClient
      .get<SpreadsheetsResponse>(
        `/credentials/${credentialId}/sheets/spreadsheets`,
        { params: { query: debouncedQuery, page_size: 100 } },
      )
      .then(({ data }) => {
        if (!alive) return
        setItems(data.spreadsheets)
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load spreadsheets'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [credentialId, debouncedQuery])

  return (
    <Modal
      open
      onClose={onClose}
      title="Pick a Google Sheet"
      description="Search your spreadsheets or create a new one."
      width="580px"
      footer={
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
      }
    >
      <div className="flex flex-col gap-3 px-6 py-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name…"
            className="pl-8 text-[12px]"
            autoFocus
          />
        </div>

        <CreateInlineRow credentialId={credentialId} onCreated={onSelect} />

        <div className="min-h-[260px] max-h-[400px] overflow-y-auto rounded-[6px] border border-border-faint bg-bg">
          {loading && !items && (
            <div className="flex h-full items-center justify-center gap-2 py-10 text-[12px] text-text-muted">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Loading spreadsheets…
            </div>
          )}
          {error && !loading && (
            <div className="px-3 py-4 text-[12px] text-[var(--err,#dc2626)]">{error}</div>
          )}
          {!loading && !error && items && items.length === 0 && (
            <div className="px-3 py-8 text-center text-[12px] text-text-muted">
              {query
                ? `No spreadsheets matching "${query}".`
                : 'No spreadsheets in your account yet — create one above.'}
            </div>
          )}
          {!error && items && items.length > 0 && (
            <ul className="divide-y divide-border-faint">
              {items.map((sheet) => (
                <li
                  key={sheet.id}
                  className="group flex items-center gap-2.5 px-3 py-2 text-[12.5px] hover:bg-surface-2"
                >
                  <FileSpreadsheet className="h-4 w-4 shrink-0 text-[#0f9d58]" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-text" title={sheet.name}>
                      {sheet.name}
                    </div>
                    {sheet.modifiedTime && (
                      <div className="truncate text-[10.5px] text-text-faint">
                        Modified {formatDate(sheet.modifiedTime)}
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => onSelect({ id: sheet.id, name: sheet.name })}
                    className={cn(
                      'rounded-[4px] border border-border-faint px-2 py-0.5 text-[10.5px] font-medium',
                      'text-text-muted opacity-0 transition-opacity',
                      'group-hover:opacity-100',
                      'hover:border-accent hover:bg-accent hover:text-bg',
                    )}
                  >
                    Select
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Modal>
  )
}

function CreateInlineRow({
  credentialId,
  onCreated,
}: {
  credentialId: string
  onCreated: (sheet: { id: string; name: string }) => void
}) {
  const [title, setTitle] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const create = async () => {
    const t = title.trim()
    if (!t || creating) return
    setError(null)
    setCreating(true)
    try {
      const { data } = await apiClient.post<CreateResponse>(
        `/credentials/${credentialId}/sheets/spreadsheets`,
        { title: t },
      )
      onCreated({ id: data.id, name: data.name })
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err.response?.data?.detail || err.message || 'Create failed')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex items-center gap-1.5 rounded-[6px] border border-dashed border-border-faint bg-surface px-2 py-1.5">
      <Plus className="h-3.5 w-3.5 shrink-0 text-text-faint" />
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') void create()
        }}
        placeholder="Create new spreadsheet…"
        className="flex-1 border-none bg-transparent text-[12px] focus:ring-0"
      />
      <Button
        size="sm"
        variant="ghost"
        onClick={() => void create()}
        disabled={creating || !title.trim()}
      >
        {creating ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Create'}
      </Button>
      {error && (
        <div
          className="ml-2 truncate text-[10.5px] text-[var(--err,#dc2626)]"
          title={error}
        >
          {error}
        </div>
      )}
    </div>
  )
}

// ── helpers ──────────────────────────────────────────────────────────────

function useDebounced<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value)
  const handle = useRef<number | undefined>(undefined)
  useEffect(() => {
    handle.current = window.setTimeout(() => setDebounced(value), ms)
    return () => {
      if (handle.current !== undefined) window.clearTimeout(handle.current)
    }
  }, [value, ms])
  return debounced
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
