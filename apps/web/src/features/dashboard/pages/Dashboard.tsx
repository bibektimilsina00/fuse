import { useNavigate } from 'react-router-dom'
import { GreetingRow }      from '../components/GreetingRow'
import { StatsGrid }        from '../components/StatsGrid'
import { PromptCard }       from '../components/PromptCard'
import { GeneratingCard }   from '../components/GeneratingCard'
import { RecentRuns }       from '../components/RecentRuns'
import { SchedulePanel }    from '../components/SchedulePanel'
import { ConnectionsPanel } from '../components/ConnectionsPanel'
import { useDashboard }     from '../hooks/useDashboard'
import { useAIGenerator }   from '../hooks/useAIGenerator'
import { APP_ROUTES }       from '@/shared/constants/routes'
import type { DashboardStat } from '../services/dashboardAPI'

const SKELETON_STATS: DashboardStat[] = [
  { label: 'Runs today',       value: '—', unit: '',   delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Success rate',     value: '—', unit: '%',  delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Time saved',       value: '—', unit: 'hr', delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Active workflows', value: '—', unit: '',   delta: '—', delta_dir: 'flat', spark: [] },
]

export function Dashboard() {
  const navigate = useNavigate()
  const { data } = useDashboard()
  const ai = useAIGenerator()

  const stats       = data?.stats       ?? SKELETON_STATS
  const recentRuns  = data?.recent_runs ?? []
  const schedules   = data?.schedules   ?? []
  const connections = data?.connections ?? []
  const totalToday  = data?.total_today ?? 0

  return (
    <div className="p-[24px_28px_28px] flex flex-col gap-[24px] max-w-[1240px] w-full mx-auto flex-1">
      <GreetingRow />
      <StatsGrid items={stats} />

      {ai.creating
        ? <GeneratingCard message={ai.message} onCancel={ai.cancel} />
        : <PromptCard onSubmit={ai.generate} />}

      <div className="grid grid-cols-[minmax(0,1fr)_320px] gap-[24px]">
        <RecentRuns
          items={recentRuns}
          totalToday={totalToday}
          onViewAll={() => navigate(APP_ROUTES.RUNS)}
        />
        <div className="flex flex-col gap-[16px]">
          <SchedulePanel
            items={schedules}
            onViewAll={() => navigate(APP_ROUTES.SCHEDULES)}
          />
          <ConnectionsPanel
            items={connections}
            totalActive={connections.filter(c => c.state === 'ok').length}
          />
        </div>
      </div>
    </div>
  )
}
