import { Icons } from '@/shared/components'
import { PanelHead } from './PanelHead'

export interface RunItem {
  status: 'ok' | 'run' | 'err' | 'warn'
  name: string
  trigger: string
  duration: string
  ago: string
}

const defaultRuns: RunItem[] = [
  { status: 'ok', name: 'Stripe refund — Slack approval', trigger: 'stripe.charge.refunded', duration: '1.4s', ago: '2m ago' },
  { status: 'ok', name: 'Lead enrichment — Clearbit → HubSpot', trigger: 'hubspot.contact.created', duration: '3.1s', ago: '4m ago' },
  { status: 'run', name: 'Inbound RFP classifier', trigger: 'imap.inbox.new', duration: 'running', ago: 'now' },
  { status: 'ok', name: 'Daily brief from Linear + GitHub', trigger: 'schedule.daily', duration: '8.7s', ago: '1h ago' },
  { status: 'err', name: 'Notion → Airtable nightly sync', trigger: 'schedule.0_2_*_*_*', duration: '12.4s', ago: '2h ago' },
  { status: 'ok', name: 'Invoice triage agent', trigger: 'gmail.label.invoice', duration: '5.9s', ago: '3h ago' },
  { status: 'warn', name: 'Support ticket auto-tagger', trigger: 'zendesk.ticket.new', duration: '2.2s', ago: '4h ago' },
  { status: 'ok', name: 'Weekly metrics digest', trigger: 'schedule.weekly', duration: '11.0s', ago: '5h ago' },
]

interface RecentRunsProps {
  items?: RunItem[]
  onOpenRun: (run: RunItem, index: number) => void
  onViewAll: () => void
}

export function RecentRuns({ items = defaultRuns, onOpenRun, onViewAll }: RecentRunsProps) {
  return (
    <div className="panel">
      <PanelHead
        icon={<Icons.Activity className="w-3.5 h-3.5" />}
        title="Recent runs"
        count="1,284 today"
        action={
          <button className="link-btn" onClick={onViewAll}>
            <span>View all</span>
            <Icons.CaretRight className="w-3 h-3" />
          </button>
        }
      />
      <div className="runs">
        {items.map((r, i) => (
          <div key={i} className="run-row" onClick={() => onOpenRun(r, i)}>
            <span className={`status-dot ${r.status}`} />
            <span className="run-name">{r.name}</span>
            <span className="run-trigger">
              <Icons.Bolt className="w-2.5 h-2.5" />
              <span>{r.trigger}</span>
            </span>
            <span className="run-meta">{r.duration}</span>
            <span className="run-meta">{r.ago}</span>
            <span className="caret">
              <Icons.CaretRight className="w-3.5 h-3.5" />
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
