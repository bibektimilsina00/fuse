import { Icons } from '@/shared/components'
import { PanelHead } from './PanelHead'

export interface ScheduleItem {
  time: string
  name: string
  sub: string
}

const defaultSchedule: ScheduleItem[] = [
  { time: '14:30', name: 'Weekly metrics digest', sub: 'linear · github · stripe' },
  { time: '16:00', name: 'Churn-risk watchlist refresh', sub: 'agent · 6 sources' },
  { time: '18:00', name: 'EOD pager rotation handoff', sub: 'pagerduty · slack' },
  { time: '02:00', name: 'Notion → Airtable sync', sub: 'scheduled · last failed' },
]

interface SchedulePanelProps {
  items?: ScheduleItem[]
  onOpenSchedule?: (item: ScheduleItem, index: number) => void
  onViewAll?: () => void
}

export function SchedulePanel({ items = defaultSchedule, onOpenSchedule, onViewAll }: SchedulePanelProps) {
  return (
    <div className="panel">
      <PanelHead
        icon={<Icons.Clock className="w-3.5 h-3.5" />}
        title="Next 12 hours"
        action={
          onViewAll && (
            <button className="link-btn" onClick={onViewAll}>
              <span>All</span>
              <Icons.CaretRight className="w-3 h-3" />
            </button>
          )
        }
      />
      <div>
        {items.map((s, i) => (
          <div
            key={i}
            className="schedule-row"
            onClick={() => onOpenSchedule?.(s, i)}
          >
            <span className="schedule-time">{s.time}</span>
            <span className="schedule-meta">
              <span className="schedule-name">{s.name}</span>
              <span className="schedule-sub">{s.sub}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
