import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { SaveState, WorkflowDetail } from '../types/editorTypes'

interface Props {
  workflow: WorkflowDetail
  saveState: SaveState
  isRunning: boolean
  onRename: (name: string) => void
  onToggle: () => void
  onRun: () => void
}

function SaveIndicator({ state }: { state: SaveState }) {
  const map = {
    saved:   { label: 'Saved',   color: 'text-[var(--ok)]' },
    saving:  { label: 'Saving…', color: 'text-[var(--text-faint)]' },
    unsaved: { label: 'Unsaved', color: 'text-[var(--warn)]' },
    error:   { label: 'Save failed', color: 'text-[var(--err)]' },
  }
  const { label, color } = map[state]
  return (
    <span className={`text-[11.5px] font-mono ${color} flex items-center gap-1.5`}>
      {state === 'saving' && (
        <span className="w-2.5 h-2.5 border border-current border-t-transparent rounded-full animate-spin" />
      )}
      {label}
    </span>
  )
}

export function EditorTopbar({ workflow, saveState, isRunning, onRename, onToggle, onRun }: Props) {
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)
  const [nameVal, setNameVal] = useState(workflow.name)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { setNameVal(workflow.name) }, [workflow.name])

  const commitRename = () => {
    setEditing(false)
    const trimmed = nameVal.trim()
    if (trimmed && trimmed !== workflow.name) onRename(trimmed)
    else setNameVal(workflow.name)
  }

  return (
    <header className="flex items-center justify-between h-[52px] px-4 bg-[var(--bg-2)] border-b border-[var(--border-faint)] shrink-0 gap-3">
      {/* Left — back + name */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={() => navigate(APP_ROUTES.AUTOMATIONS)}
          className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors shrink-0"
          title="Back to automations"
        >
          <Icons.CaretRight style={{ width: 13, height: 13, transform: 'rotate(180deg)' }} />
        </button>

        {/* Workflow name — click to rename */}
        {editing ? (
          <input
            ref={inputRef}
            autoFocus
            value={nameVal}
            onChange={e => setNameVal(e.target.value)}
            onBlur={commitRename}
            onKeyDown={e => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') { setNameVal(workflow.name); setEditing(false) } }}
            className="bg-transparent border-b border-[var(--border)] outline-none text-[14px] font-semibold text-[var(--text)] tracking-tight min-w-0 w-[240px]"
          />
        ) : (
          <span
            className="text-[14px] font-semibold text-[var(--text)] tracking-tight cursor-pointer hover:text-[var(--text-mute)] transition-colors truncate max-w-[280px]"
            onDoubleClick={() => setEditing(true)}
            title="Double-click to rename"
          >
            {workflow.name}
          </span>
        )}

        {/* Active badge */}
        <span className={`shrink-0 text-[9.5px] font-mono font-semibold tracking-widest uppercase px-[7px] py-[3px] pb-[2px] rounded-[4px] ${workflow.is_active ? 'bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]' : 'bg-[var(--surface-2)] text-[var(--text-dim)]'}`}>
          {workflow.is_active ? 'Active' : 'Draft'}
        </span>
      </div>

      {/* Center — save status */}
      <SaveIndicator state={saveState} />

      {/* Right — actions */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Toggle active */}
        <button
          onClick={onToggle}
          className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-[8px] text-[12.5px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] hover:text-[var(--text)] transition-colors"
        >
          {workflow.is_active ? <Icons.Pause style={{ width: 12, height: 12 }} /> : <Icons.Activity style={{ width: 12, height: 12 }} />}
          {workflow.is_active ? 'Pause' : 'Activate'}
        </button>

        {/* Run */}
        <button
          onClick={onRun}
          disabled={isRunning}
          className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-[8px] text-[12.5px] font-medium bg-[var(--text)] text-[var(--bg)] border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-50 disabled:cursor-default"
        >
          {isRunning ? (
            <><span className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" /> Running…</>
          ) : (
            <><Icons.Activity style={{ width: 12, height: 12 }} /> Run</>
          )}
        </button>
      </div>
    </header>
  )
}
