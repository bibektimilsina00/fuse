import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronLeft, ChevronDown, Play, Loader2,
  Pencil, Copy, Download, Trash2, Activity,
  Check, Cloud, Clock,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { Button, Dropdown, DropdownTrigger, DropdownContent, DropdownItem, DropdownSeparator } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'
import type { SaveState } from '../../types/editorTypes'

interface EditorTopbarProps {
  workflowName: string
  isActive: boolean
  saveState: SaveState
  versionVector: number
  isRunning: boolean
  onRun: () => void
  onToggleActive: () => void
  onRename: (name: string) => void
  className?: string
}

function SaveStatus({ saveState }: { saveState: SaveState }) {
  if (saveState === 'saving') {
    return (
      <span className="flex items-center gap-1.5 text-[11px] text-[var(--text-mute)]">
        <Loader2 className="h-3 w-3 animate-spin" />
        Saving…
      </span>
    )
  }
  if (saveState === 'error') {
    return (
      <span className="flex items-center gap-1.5 text-[11px] text-[var(--danger)]">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--danger)]" />
        Save failed
      </span>
    )
  }
  if (saveState === 'unsaved') {
    return (
      <span className="flex items-center gap-1.5 text-[11px] text-[var(--text-mute)]">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--warn)]" />
        Unsaved
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1.5 text-[11px] text-[var(--text-mute)]">
      <Cloud className="h-3 w-3 text-[var(--text-faint)]" />
      Synced
    </span>
  )
}

export function EditorTopbar({
  workflowName,
  isActive,
  saveState,
  versionVector,
  isRunning,
  onRun,
  onToggleActive,
  onRename,
  className,
}: EditorTopbarProps) {
  const navigate = useNavigate()
  const [renaming, setRenaming] = useState(false)
  const [nameValue, setNameValue] = useState(workflowName)
  const [stateOpen, setStateOpen] = useState(false)

  const handleRenameCommit = () => {
    const trimmed = nameValue.trim()
    if (trimmed && trimmed !== workflowName) onRename(trimmed)
    setRenaming(false)
  }

  return (
    <header
      className={cn(
        'relative z-20 flex h-[52px] shrink-0 items-center justify-between gap-3 border-b border-[var(--border-faint)] bg-[var(--bg)] px-3',
        className,
      )}
    >
      {/* ── Left ──────────────────────────────────────────── */}
      <div className="flex min-w-0 items-center gap-1">
        <button
          onClick={() => navigate(APP_ROUTES.AUTOMATIONS)}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
          title="Back to automations"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        <span className="text-[12.5px] text-[var(--text-mute)]">Automations</span>
        <span className="text-[11px] text-[var(--text-dim)]">/</span>

        {/* Workflow name + dropdown */}
        <Dropdown>
          <DropdownTrigger>
            <button className="flex h-8 max-w-[280px] items-center gap-1.5 rounded-[7px] px-2 py-1 text-[12.5px] font-medium text-[var(--text)] transition-colors hover:bg-[var(--surface)]">
              {renaming ? (
                <input
                  autoFocus
                  value={nameValue}
                  onChange={e => setNameValue(e.target.value)}
                  onBlur={handleRenameCommit}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleRenameCommit()
                    if (e.key === 'Escape') { setNameValue(workflowName); setRenaming(false) }
                    e.stopPropagation()
                  }}
                  onClick={e => e.stopPropagation()}
                  className="w-full bg-transparent outline-none"
                />
              ) : (
                <>
                  <span className="truncate">{workflowName}</span>
                  <ChevronDown className="h-3 w-3 shrink-0 text-[var(--text-faint)]" />
                </>
              )}
            </button>
          </DropdownTrigger>
          <DropdownContent className="w-56">
            <DropdownItem onClick={() => setRenaming(true)} leftIcon={<Pencil />}>
              Rename
            </DropdownItem>
            <DropdownItem onClick={() => {}} leftIcon={<Copy />}>
              Duplicate
            </DropdownItem>
            <DropdownItem onClick={() => {}} leftIcon={<Download />}>
              Export as JSON
            </DropdownItem>
            <DropdownItem onClick={() => {}} leftIcon={<Activity />}>
              View runs
            </DropdownItem>
            <DropdownSeparator />
            <DropdownItem onClick={() => {}} variant="danger" leftIcon={<Trash2 />}>
              Delete workflow
            </DropdownItem>
          </DropdownContent>
        </Dropdown>

        {/* Active / Paused pill */}
        <Dropdown open={stateOpen} onOpenChange={setStateOpen}>
          <DropdownTrigger>
            <button
              className={cn(
                'flex items-center gap-1.5 rounded-[6px] border px-2 py-1 text-[11.5px] font-medium leading-none transition-colors',
                'border-[var(--border-faint)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--surface-2)]',
              )}
            >
              <span
                className={cn('h-1.5 w-1.5 rounded-full', isActive ? 'bg-[var(--success)]' : 'bg-[var(--warn)]')}
              />
              {isActive ? 'Active' : 'Paused'}
              <ChevronDown className="h-2.5 w-2.5 text-[var(--text-faint)]" />
            </button>
          </DropdownTrigger>
          <DropdownContent className="w-52">
            <button
              onClick={() => { if (!isActive) { onToggleActive(); } setStateOpen(false) }}
              className="flex w-full items-center gap-2.5 rounded-[7px] px-2.5 py-2 text-[12.5px] transition-colors hover:bg-[var(--surface)]"
            >
              <span className="h-2 w-2 rounded-full bg-[var(--success)]" />
              <span className="flex-1 text-left">
                <span className="block font-medium">Active</span>
                <span className="text-[10.5px] text-[var(--text-faint)]">Triggers will fire</span>
              </span>
              {isActive && <Check className="h-3.5 w-3.5 text-[var(--text-mute)]" />}
            </button>
            <button
              onClick={() => { if (isActive) { onToggleActive(); } setStateOpen(false) }}
              className="flex w-full items-center gap-2.5 rounded-[7px] px-2.5 py-2 text-[12.5px] transition-colors hover:bg-[var(--surface)]"
            >
              <span className="h-2 w-2 rounded-full bg-[var(--warn)]" />
              <span className="flex-1 text-left">
                <span className="block font-medium">Paused</span>
                <span className="text-[10.5px] text-[var(--text-faint)]">Triggers ignored</span>
              </span>
              {!isActive && <Check className="h-3.5 w-3.5 text-[var(--text-mute)]" />}
            </button>
          </DropdownContent>
        </Dropdown>
      </div>

      {/* ── Center ────────────────────────────────────────── */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <div className="flex items-center gap-2 rounded-full border border-[var(--border-faint)] bg-[var(--bg-2)] px-3 py-1.5">
          <SaveStatus saveState={saveState} />
          {versionVector > 0 && (
            <>
              <span className="text-[var(--text-dim)]">·</span>
              <span className="font-mono text-[10.5px] text-[var(--text-mute)]">v{versionVector}</span>
            </>
          )}
        </div>
      </div>

      {/* ── Right ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        <Button
          variant="primary"
          size="sm"
          onClick={onRun}
          disabled={isRunning}
          leftIcon={isRunning ? <Loader2 className="animate-spin" /> : <Play />}
        >
          {isRunning ? 'Running' : 'Run'}
        </Button>
      </div>
    </header>
  )
}
