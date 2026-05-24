import { Play, Loader2 } from 'lucide-react'
import { Button } from '@/shared/components'

interface TestPanelProps {
  onRun: () => void
  isRunning: boolean
}

export function TestPanel({ onRun, isRunning }: TestPanelProps) {
  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div>
        <p className="text-[13px] font-medium text-[var(--text)]">Test workflow</p>
        <p className="mt-1 text-[12px] text-[var(--text-mute)]">
          Run a single test execution with a manual trigger. Logs appear in the Logs tab.
        </p>
      </div>

      <Button
        variant="primary"
        onClick={onRun}
        disabled={isRunning}
        leftIcon={isRunning ? <Loader2 className="animate-spin" /> : <Play />}
      >
        {isRunning ? 'Running…' : 'Run workflow'}
      </Button>
    </div>
  )
}
