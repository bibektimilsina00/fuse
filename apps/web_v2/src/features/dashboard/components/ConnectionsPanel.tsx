import { Icons } from '@/shared/components'
import { PanelHead } from './PanelHead'

export interface ConnectionItem {
  id: string
  name: string
  sub: string
  state: 'ok' | 'warn' | 'err'
}

const defaultConnections: ConnectionItem[] = [
  { id: 'stripe', name: 'Stripe', sub: '12 endpoints · 4 webhooks', state: 'ok' },
  { id: 'slack', name: 'Slack', sub: '3 workspaces', state: 'ok' },
  { id: 'linear', name: 'Linear', sub: 'fuse-engineering', state: 'ok' },
  { id: 'notion', name: 'Notion', sub: 'token expires in 4d', state: 'warn' },
  { id: 'hub', name: 'HubSpot', sub: 'auth failed · re-link', state: 'err' },
]

interface ConnectionsPanelProps {
  items?: ConnectionItem[]
  onManageConnections: () => void
}

export function ConnectionsPanel({ items = defaultConnections, onManageConnections }: ConnectionsPanelProps) {
  return (
    <div className="panel">
      <PanelHead
        icon={<Icons.Plug className="w-3.5 h-3.5" />}
        title="Connections"
        count="18 active"
        action={
          <button className="link-btn" onClick={onManageConnections}>
            <span>Manage</span>
            <Icons.CaretRight className="w-3 h-3" />
          </button>
        }
      />
      <div>
        {items.map((c, i) => (
          <div key={i} className="conn-row">
            <span className={`conn-icon ${c.id}`}>{c.name.slice(0, 2)}</span>
            <span className="conn-meta">
              <span className="conn-name">{c.name}</span>
              <span className="conn-sub">{c.sub}</span>
            </span>
            <span className={`conn-state ${c.state}`}>{c.state}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
