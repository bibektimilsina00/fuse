import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { Select } from '@/shared/components'
import type { RendererProps } from '../types'

/**
 * Field renderer for the `wa-template` property type — lets WhatsApp
 * action nodes pick a pre-approved message template registered against
 * the user's WhatsApp Business Account.
 *
 * Two upstream dependencies are read from `properties`:
 *   - `credential`  — the meta_oauth credential id
 *   - `waba_id`     — the WhatsApp Business Account id selected via a
 *                     `meta-resource` field (resourceKind=waba)
 *
 * The saved value is the template `name` (string). The `language_code`
 * and `body_variables` live on separate sibling fields — the renderer
 * doesn't try to manage them, since templates can change shape between
 * approval cycles and we don't want stale variable counts overwriting
 * user-entered values.
 */

interface WATemplate {
  id: string
  name: string
  language: string
  status: string
  category: string | null
  body_variable_count: number
  body_preview: string
  raw: unknown
}

interface WATemplatesResponse {
  credential_id: string
  waba_id: string
  templates: WATemplate[]
}

const STATUS_STYLES: Record<string, string> = {
  APPROVED: 'bg-ok/10 text-ok border-ok/30',
  PENDING: 'bg-warn/10 text-warn border-warn/30',
  REJECTED: 'bg-err/10 text-err border-err/30',
  PAUSED: 'bg-surface text-text-mute border-border-faint',
  DISABLED: 'bg-surface text-text-mute border-border-faint',
}

export function WATemplateRenderer({ properties, value, onChange, disabled }: RendererProps) {
  const credentialId = readString(properties.credential)
  const wabaId = readString(properties.waba_id)

  const query = useQuery({
    queryKey: ['meta-wa-templates', credentialId, wabaId],
    queryFn: async (): Promise<WATemplate[]> => {
      if (!credentialId || !wabaId) return []
      const res = await apiClient.get<WATemplatesResponse>(API_ROUTES.META_WA_TEMPLATES, {
        params: { credential_id: credentialId, waba_id: wabaId },
      })
      return res.data?.templates ?? []
    },
    enabled: Boolean(credentialId && wabaId),
    staleTime: 1000 * 60,
  })

  const templates = useMemo(() => query.data ?? [], [query.data])
  const selected = useMemo(
    () => templates.find(t => t.name === readString(value)),
    [templates, value],
  )

  if (!credentialId) {
    return (
      <p className="text-[11.5px] text-text-faint">
        Pick a Meta account above to load templates.
      </p>
    )
  }
  if (!wabaId) {
    return (
      <p className="text-[11.5px] text-text-faint">
        Pick a WhatsApp Business Account to load its templates.
      </p>
    )
  }

  if (query.isLoading) {
    return (
      <div className="flex h-9 items-center gap-2 rounded-[7px] border border-border-faint bg-bg px-3 text-[12px] text-text-faint">
        <Loader2 size={13} className="animate-spin" />
        Loading templates…
      </div>
    )
  }

  if (query.isError) {
    return (
      <p className="rounded-[7px] border border-err/30 bg-err/10 px-2.5 py-1.5 text-[11.5px] text-err">
        {query.error instanceof Error ? query.error.message : 'Failed to load templates.'}
      </p>
    )
  }

  if (templates.length === 0) {
    return (
      <p className="rounded-[7px] border border-dashed border-border-faint bg-bg px-2.5 py-1.5 text-[11.5px] text-text-faint">
        No templates registered for this WhatsApp Business Account.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Select
        value={readString(value) ?? ''}
        onChange={onChange}
        disabled={disabled}
        placeholder="Select a template…"
        options={templates.map(t => ({
          value: t.name,
          label: `${t.name} · ${t.language} (${t.status})`,
        }))}
        className="w-full"
      />

      {selected && (
        <div className="flex flex-col gap-1 rounded-[7px] border border-border-faint bg-bg p-2">
          <div className="flex items-center justify-between gap-2">
            <span
              className={cn(
                'rounded-[4px] border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide',
                STATUS_STYLES[selected.status] ?? STATUS_STYLES.PAUSED,
              )}
            >
              {selected.status}
            </span>
            <span className="text-[10.5px] text-text-faint">
              {selected.body_variable_count} variable{selected.body_variable_count === 1 ? '' : 's'}
              {selected.category ? ` · ${selected.category}` : ''}
            </span>
          </div>
          {selected.body_preview && (
            <p className="whitespace-pre-line text-[11.5px] text-text-mute">
              {selected.body_preview}
            </p>
          )}
          {selected.status !== 'APPROVED' && (
            <p className="text-[10.5px] text-warn">
              Only APPROVED templates can be sent. Meta will reject this at send time.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function readString(v: unknown): string {
  if (typeof v === 'string') return v
  if (v == null) return ''
  return String(v)
}
