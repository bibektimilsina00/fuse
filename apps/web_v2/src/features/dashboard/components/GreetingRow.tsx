import { useAuth } from '@/features/auth/hooks/useAuth'
import { Icons } from '@/shared/components'

interface GreetingRowProps {
  onNewAutomation: () => void
  onConnectApp: () => void
}

export function GreetingRow({ onNewAutomation, onConnectApp }: GreetingRowProps) {
  const { user } = useAuth()
  
  // Format current date: e.g. "Wed, May 21"
  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })

  // Determine greeting based on local time
  const hour = new Date().getHours()
  let greetingText = 'Good morning'
  if (hour >= 12 && hour < 17) {
    greetingText = 'Good afternoon'
  } else if (hour >= 17 || hour < 4) {
    greetingText = 'Good evening'
  }

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'Mahesh'

  return (
    <div className="greeting-row">
      <div className="greeting">
        <span className="eyebrow">
          <span className="dot animate-status-pulse" />
          All systems operational · {formattedDate}
        </span>
        <h1>
          {greetingText}, {firstName}
          <span style={{ color: 'var(--accent)' }}>.</span>
        </h1>
      </div>
      <div className="btn-group">
        <button className="btn btn-secondary" onClick={onConnectApp}>
          <Icons.Plug className="w-3.5 h-3.5" />
          <span>Connect app</span>
        </button>
        <button className="btn btn-primary" onClick={onNewAutomation}>
          <Icons.Plus className="w-3.5 h-3.5" />
          <span>New automation</span>
        </button>
      </div>
    </div>
  )
}
