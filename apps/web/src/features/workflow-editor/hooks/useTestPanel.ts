import { useState, useCallback } from 'react'

export interface TestVar {
  k: string
  v: string
}

export interface TestScenario {
  id: string
  name: string
  desc: string
  payload: string
  vars: TestVar[]
  mockCalls: boolean
  replayLast: boolean
  lastRun: { status: 'ok' | 'err'; t: string } | null
}

const INITIAL: TestScenario[] = [
  {
    id: 't1',
    name: 'Default scenario',
    desc: '',
    payload: '{\n  \n}',
    vars: [],
    mockCalls: true,
    replayLast: false,
    lastRun: null,
  },
]

export function useTestPanel(onRun: () => void) {
  const [scenarios, setScenarios] = useState<TestScenario[]>(INITIAL)
  const [selectedId, setSelectedId] = useState(INITIAL[0].id)
  const [renameId, setRenameId] = useState<string | null>(null)

  const selected = scenarios.find(s => s.id === selectedId) ?? scenarios[0]

  const patchSelected = useCallback((patch: Partial<TestScenario>) => {
    setScenarios(ss => ss.map(s => s.id === selectedId ? { ...s, ...patch } : s))
  }, [selectedId])

  const renameScenario = useCallback((id: string, name: string) => {
    setScenarios(ss => ss.map(s => s.id === id ? { ...s, name } : s))
  }, [])

  const setVar = useCallback((i: number, field: 'k' | 'v', value: string) => {
    setScenarios(ss => ss.map(s =>
      s.id === selectedId
        ? { ...s, vars: s.vars.map((row, idx) => idx === i ? { ...row, [field]: value } : row) }
        : s,
    ))
  }, [selectedId])

  const addVar = useCallback(() => {
    patchSelected({ vars: [...selected.vars, { k: '', v: '' }] })
  }, [patchSelected, selected.vars])

  const removeVar = useCallback((i: number) => {
    patchSelected({ vars: selected.vars.filter((_, idx) => idx !== i) })
  }, [patchSelected, selected.vars])

  const addScenario = useCallback(() => {
    const id = crypto.randomUUID()
    const s: TestScenario = {
      id, name: 'Untitled scenario', desc: '',
      payload: '{\n  \n}', vars: [],
      mockCalls: true, replayLast: false, lastRun: null,
    }
    setScenarios(ss => [...ss, s])
    setSelectedId(id)
    setRenameId(id)
  }, [])

  const duplicateScenario = useCallback((id?: string) => {
    const target = id ? (scenarios.find(s => s.id === id) ?? selected) : selected
    const nextId = crypto.randomUUID()
    const dup: TestScenario = { ...target, id: nextId, name: target.name + ' (copy)', lastRun: null }
    setScenarios(ss => [...ss, dup])
    setSelectedId(nextId)
  }, [selected, scenarios])

  const deleteScenario = useCallback((id?: string) => {
    const targetId = id ?? selectedId
    if (scenarios.length <= 1) return
    const remaining = scenarios.filter(s => s.id !== targetId)
    setScenarios(remaining)
    if (targetId === selectedId) {
      setSelectedId(remaining[0].id)
    }
  }, [scenarios, selectedId])

  const runScenario = useCallback(() => {
    onRun()
    patchSelected({ lastRun: { status: 'ok', t: 'Just now' } })
  }, [onRun, patchSelected])

  return {
    scenarios,
    selected,
    selectedId,
    setSelectedId,
    renameId,
    setRenameId,
    renameScenario,
    patchSelected,
    setVar,
    addVar,
    removeVar,
    addScenario,
    duplicateScenario,
    deleteScenario,
    runScenario,
  }
}
