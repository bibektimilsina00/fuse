import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
  Plus,
  X,
  ChevronDown,
  ChevronRight,
  Search,
  Server,
  ArrowLeft,
  Edit2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ToolConfig } from '@fuse/node-definitions'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import { useAvailableTools } from './use-available-tools'
import { useCreateSkill } from '@/hooks/skills/queries'
import type { Skill } from '@/hooks/skills/queries'
import type { SelectedTool } from './types'
import { useEditorLayout } from '../../hooks/use-editor-layout'
import { PropertyGroupList } from '../PropertyGroupList'
import type { CanonicalModeOverrides } from '../../visibility'

// Shared input style used across inline forms in this file
const INPUT_CLASS =
  'w-full bg-surface-editor border border-border rounded px-2 h-[28px] text-[12px] text-white placeholder:text-text-placeholder focus:outline-none focus:border-border-strong transition-colors'

function resolveEntryAppearance(
  tool: SelectedTool,
  toolConfig?: ToolConfig,
): { icon: string; color: string } | null {
  const kind = tool.kind ?? 'tool'
  if (kind === 'tool' && toolConfig) return { icon: toolConfig.icon, color: toolConfig.color }
  if (!tool.icon || !tool.color) return null
  return { icon: tool.icon, color: tool.color }
}

// Rendered icon box — identical to NodeHeader's colored icon square
const EntryIcon: React.FC<{ icon: string; color: string }> = ({ icon, color }) => (
  <div
    className="flex size-[22px] shrink-0 items-center justify-center rounded-md"
    style={{ background: color }}
  >
    {React.cloneElement(getIcon(icon) as React.ReactElement, { className: 'size-[13px] text-white' })}
  </div>
)

const MissingEntryIcon: React.FC = () => (
  <div
    className="flex size-[22px] shrink-0 items-center justify-center rounded-md border border-red-400/60 text-[10px] font-bold text-red-300"
    title="Missing icon/color metadata"
  >
    !
  </div>
)

const EntryAppearanceIcon: React.FC<{ appearance: { icon: string; color: string } | null }> = ({
  appearance,
}) => (appearance ? <EntryIcon {...appearance} /> : <MissingEntryIcon />)


// ---------------------------------------------------------------------------
// UsageControlToggle
// ---------------------------------------------------------------------------

type UsageControl = 'auto' | 'force' | 'none'

const USAGE_OPTIONS: { label: string; value: UsageControl }[] = [
  { label: 'Auto', value: 'auto' },
  { label: 'Force', value: 'force' },
  { label: 'None', value: 'none' },
]

const UsageControlToggle: React.FC<{ value: UsageControl; onChange: (v: UsageControl) => void }> = ({
  value,
  onChange,
}) => (
  <div
    className="flex items-center rounded overflow-hidden border border-border text-[10px] font-semibold shrink-0"
    onClick={(e) => e.stopPropagation()}
  >
    {USAGE_OPTIONS.map((opt) => (
      <button
        key={opt.value}
        onClick={() => onChange(opt.value)}
        className={cn(
          'px-1.5 h-5 transition-colors',
          value === opt.value
            ? opt.value === 'force'
              ? 'bg-orange-500/20 text-orange-300'
              : 'bg-surface-5 text-white'
            : 'bg-transparent text-text-muted hover:text-white',
        )}
      >
        {opt.label}
      </button>
    ))}
  </div>
)

// ---------------------------------------------------------------------------
// ToolCard — registry tool (kind='tool')
// Uses the exact same PropertyField + useEditorLayout as the node EditorTab.
// ---------------------------------------------------------------------------

interface ToolCardProps {
  tool: SelectedTool
  toolConfig: ToolConfig | undefined
  onRemove: () => void
  onToggleExpand: () => void
  onParamChange: (key: string, value: unknown) => void
  onUsageControlChange: (value: UsageControl) => void
}

const ToolCard: React.FC<ToolCardProps> = ({
  tool,
  toolConfig,
  onRemove,
  onToggleExpand,
  onParamChange,
  onUsageControlChange,
}) => {
  const usageControl: UsageControl = tool.usageControl ?? 'auto'
  const [canonicalModes, setCanonicalModes] = useState<CanonicalModeOverrides>({})

  // Build synthetic NodeDefinition from ToolConfig so useEditorLayout works identically
  const definition = React.useMemo(
    () =>
      toolConfig
        ? {
            type: toolConfig.id,
            name: toolConfig.name,
            category: 'integration' as const,
            description: toolConfig.description,
            icon: toolConfig.icon,
            credentialType: toolConfig.credentialType,
            properties: toolConfig.properties,
            inputs: 0,
            outputs: 0,
          }
        : null,
    [toolConfig],
  )

  const params = tool.params as Record<string, any>

  // Same layout logic as EditorTab — handles conditions, canonical pairs, advanced fields
  const { mainGroups, canonicalIndex } = useEditorLayout(definition, params, canonicalModes)

  const toggleCanonicalMode = (canonicalId: string, current: 'basic' | 'advanced') => {
    setCanonicalModes((prev) => ({ ...prev, [canonicalId]: current === 'basic' ? 'advanced' : 'basic' }))
  }

  return (
    <div
      className={cn(
        'flex flex-col rounded-md border border-border bg-surface-editor overflow-hidden animate-in fade-in slide-in-from-top-1 duration-200',
        usageControl === 'none' && 'opacity-50',
      )}
    >
      <div
        className="flex items-center justify-between px-3 h-9 bg-surface-active cursor-pointer"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <EntryAppearanceIcon appearance={resolveEntryAppearance(tool, toolConfig)} />
          <span className="text-[12px] font-bold text-white truncate">{tool.title}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <UsageControlToggle value={usageControl} onChange={onUsageControlChange} />
          <button
            onClick={(e) => { e.stopPropagation(); onRemove() }}
            className="p-1.5 rounded hover:bg-surface-5 text-text-muted hover:text-red-400 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
          <div className="p-1.5 text-text-muted">
            {tool.isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </div>
        </div>
      </div>

      {tool.isExpanded && definition && (
        <div className="border-t border-border bg-[var(--bg)] p-4">
          {mainGroups.flatMap((g) => g.props).length === 0 && (
            <p className="text-[13px] text-text-muted text-center py-4">No configurable parameters.</p>
          )}
          <PropertyGroupList
            groups={mainGroups}
            selectedNode={{ id: tool.toolId ?? 'tool', type: toolConfig?.id ?? 'tool', data: {} }}
            definition={definition as any}
            properties={params}
            canonicalIndex={canonicalIndex}
            canonicalModes={canonicalModes}
            onPropertyChange={onParamChange}
            onCanonicalToggle={toggleCanonicalMode}
          />
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// SkillCard — custom tool/skill (kind='skill')
// ---------------------------------------------------------------------------

interface SkillCardProps {
  tool: SelectedTool
  onRemove: () => void
}

const SkillCard: React.FC<SkillCardProps> = ({ tool, onRemove }) => (
  <div className="flex items-center justify-between px-3 h-9 rounded-md border border-border bg-surface-editor animate-in fade-in slide-in-from-top-1 duration-200">
    <div className="flex items-center gap-2 flex-1 min-w-0">
      <EntryAppearanceIcon appearance={resolveEntryAppearance(tool)} />
      <span className="text-[12px] font-bold text-white truncate">{tool.title}</span>
      <span className="text-[10px] text-text-muted shrink-0">tool</span>
    </div>
    <button
      onClick={onRemove}
      className="p-1.5 rounded hover:bg-surface-5 text-text-muted hover:text-red-400 transition-colors"
    >
      <X className="w-3.5 h-3.5" />
    </button>
  </div>
)

// ---------------------------------------------------------------------------
// McpServerCard — MCP server entry (kind='mcp')
// ---------------------------------------------------------------------------

interface McpServerCardProps {
  tool: SelectedTool
  onRemove: () => void
  onUpdate: (updates: Partial<SelectedTool>) => void
}

const McpServerCard: React.FC<McpServerCardProps> = ({ tool, onRemove, onUpdate }) => {
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(tool.mcpName ?? '')
  const [url, setUrl] = useState(tool.mcpUrl ?? '')
  const [apiKey, setApiKey] = useState(tool.mcpApiKey ?? '')

  const save = () => {
    if (!name.trim() || !url.trim()) return
    onUpdate({ mcpName: name.trim(), mcpUrl: url.trim(), mcpApiKey: apiKey.trim() || undefined, title: name.trim() })
    setEditing(false)
  }

  return (
    <div className="flex flex-col rounded-md border border-border bg-surface-editor overflow-hidden animate-in fade-in slide-in-from-top-1 duration-200">
      <div className="flex items-center justify-between px-3 h-9 bg-surface-active">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <EntryAppearanceIcon appearance={resolveEntryAppearance(tool)} />
          <span className="text-[12px] font-bold text-white truncate">{tool.title}</span>
          <span className="text-[10px] text-text-muted shrink-0">MCP</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setEditing((v) => !v)}
            className="p-1.5 rounded hover:bg-surface-5 text-text-muted hover:text-white transition-colors"
            title="Edit"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onRemove}
            className="p-1.5 rounded hover:bg-surface-5 text-text-muted hover:text-red-400 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {!editing && (
        <div className="px-3 py-2 border-t border-border">
          <p className="text-[11px] text-text-muted truncate">{tool.mcpUrl}</p>
        </div>
      )}

      {editing && (
        <div className="px-3 py-3 border-t border-border flex flex-col gap-2">
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-text-muted">Name *</label>
            <input className={INPUT_CLASS} value={name} onChange={(e) => setName(e.target.value)} placeholder="my-server" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-text-muted">URL *</label>
            <input className={INPUT_CLASS} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://mcp.example.com" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-text-muted">API Key</label>
            <input type="password" className={INPUT_CLASS} value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="optional" />
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setEditing(false)} className="px-2 h-6 text-[11px] text-text-muted hover:text-white transition-colors">Cancel</button>
            <button
              onClick={save}
              disabled={!name.trim() || !url.trim()}
              className={cn('px-3 h-6 rounded text-[11px] font-semibold transition-colors', name.trim() && url.trim() ? 'bg-primary text-white hover:bg-primary/90' : 'bg-surface-5 text-text-muted cursor-not-allowed')}
            >
              Save
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// AddMcpForm — inline MCP server form inside combobox
// ---------------------------------------------------------------------------

interface AddMcpFormProps {
  onAdd: (entry: SelectedTool) => void
  onBack: () => void
}

const AddMcpForm: React.FC<AddMcpFormProps> = ({ onAdd, onBack }) => {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const nameRef = useRef<HTMLInputElement>(null)

  useEffect(() => { nameRef.current?.focus() }, [])

  const submit = () => {
    if (!name.trim() || !url.trim()) return
    onAdd({ kind: 'mcp', title: name.trim(), mcpName: name.trim(), mcpUrl: url.trim(), mcpApiKey: apiKey.trim() || undefined, params: {} })
  }

  return (
    <div className="flex flex-col" onClick={(e) => e.stopPropagation()}>
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
        <button onClick={onBack} className="p-1 rounded hover:bg-surface-5 text-text-muted hover:text-white transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
        </button>
        <span className="text-[12px] font-bold text-white">Add MCP Server</span>
      </div>
      <div className="flex flex-col gap-3 px-3 py-3">
        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold text-text-muted">Name *</label>
          <input ref={nameRef} className={INPUT_CLASS} value={name} onChange={(e) => setName(e.target.value)} placeholder="my-server" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold text-text-muted">Server URL *</label>
          <input className={INPUT_CLASS} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://mcp.example.com" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold text-text-muted">API Key <span className="font-normal">(optional)</span></label>
          <input type="password" className={INPUT_CLASS} value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-..." />
        </div>
        <button
          onClick={submit}
          disabled={!name.trim() || !url.trim()}
          className={cn('w-full h-8 rounded text-[12px] font-semibold transition-colors', name.trim() && url.trim() ? 'bg-primary text-white hover:bg-primary/90' : 'bg-surface-5 text-text-muted cursor-not-allowed')}
        >
          Add Server
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// CreateToolForm — inline tool/skill creator inside combobox
// ---------------------------------------------------------------------------

interface CreateToolFormProps {
  onCreated: (skill: Skill) => void
  onBack: () => void
}

const CreateToolForm: React.FC<CreateToolFormProps> = ({ onCreated, onBack }) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [content, setContent] = useState('')
  const nameRef = useRef<HTMLInputElement>(null)
  const createSkill = useCreateSkill()

  useEffect(() => { nameRef.current?.focus() }, [])

  const isValidName = /^[a-z0-9]+(-[a-z0-9]+)*$/.test(name.trim())
  const canSubmit = isValidName && content.trim() && !createSkill.isPending

  const submit = () => {
    if (!canSubmit) return
    createSkill.mutate(
      { name: name.trim(), description: description.trim(), content: content.trim() },
      { onSuccess: (skill) => onCreated(skill) },
    )
  }

  return (
    <div className="flex flex-col" onClick={(e) => e.stopPropagation()}>
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
        <button onClick={onBack} className="p-1 rounded hover:bg-surface-5 text-text-muted hover:text-white transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
        </button>
        <span className="text-[12px] font-bold text-white">Create Tool</span>
      </div>

      <div className="flex flex-col gap-3 px-3 py-3">
        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold text-text-muted">Name * <span className="font-normal">(kebab-case)</span></label>
          <input
            ref={nameRef}
            className={INPUT_CLASS}
            value={name}
            onChange={(e) => setName(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
            placeholder="my-tool"
          />
          {name && !isValidName && (
            <p className="text-[10px] text-red-400">Lowercase letters, numbers and hyphens only</p>
          )}
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold text-text-muted">Description</label>
          <input
            className={INPUT_CLASS}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What this tool does"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold text-text-muted">Instructions (Markdown) *</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={5}
            placeholder={'# My Tool\n\nDescribe what the agent should do when this tool is loaded.'}
            className="w-full bg-surface-editor border border-border rounded px-2 py-1.5 text-[12px] text-white font-mono placeholder:text-text-placeholder focus:outline-none focus:border-border-strong transition-colors resize-none"
          />
        </div>

        {createSkill.isError && (
          <p className="text-[11px] text-red-400">Failed to create tool. Name may already exist.</p>
        )}

        <button
          onClick={submit}
          disabled={!canSubmit}
          className={cn(
            'w-full h-8 rounded text-[12px] font-semibold transition-colors',
            canSubmit ? 'bg-primary text-white hover:bg-primary/90' : 'bg-surface-5 text-text-muted cursor-not-allowed',
          )}
        >
          {createSkill.isPending ? 'Creating…' : 'Create Tool'}
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ToolCombobox — unified picker
// ---------------------------------------------------------------------------

type ComboView = 'list' | 'mcp' | 'create'

interface ToolComboboxProps {
  builtinTools: ToolConfig[]
  integrations: ToolConfig[]
  selectedToolIds: Set<string>
  onSelectTool: (tool: ToolConfig) => void
  onAddMcp: (entry: SelectedTool) => void
  onAddSkill: (skill: Skill) => void
  onClose: () => void
}

const ToolCombobox: React.FC<ToolComboboxProps> = ({
  builtinTools,
  integrations,
  selectedToolIds,
  onSelectTool,
  onAddMcp,
  onAddSkill,
  onClose,
}) => {
  const [view, setView] = useState<ComboView>('list')
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { if (view === 'list') inputRef.current?.focus() }, [view])

  const matches = useCallback(
    (tool: ToolConfig) => {
      if (!query) return true
      const q = query.toLowerCase()
      return tool.name.toLowerCase().includes(q) || tool.description.toLowerCase().includes(q)
    },
    [query],
  )

  const filteredBuiltin = builtinTools.filter(matches)
  const filteredIntegrations = integrations.filter(matches)
  const hasResults = filteredBuiltin.length > 0 || filteredIntegrations.length > 0

  if (view === 'create') {
    return (
      <CreateToolForm
        onCreated={(skill) => { onAddSkill(skill); onClose() }}
        onBack={() => setView('list')}
      />
    )
  }

  if (view === 'mcp') {
    return (
      <AddMcpForm
        onAdd={(entry) => { onAddMcp(entry); onClose() }}
        onBack={() => setView('list')}
      />
    )
  }

  const renderToolBtn = (toolConfig: ToolConfig) => {
    const isAdded = selectedToolIds.has(toolConfig.id)
    return (
      <button
        key={toolConfig.id}
        disabled={isAdded}
        onClick={() => { if (!isAdded) { onSelectTool(toolConfig); onClose() } }}
        className={cn(
          'w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors',
          isAdded ? 'opacity-40 cursor-default' : 'hover:bg-surface-5 cursor-pointer',
        )}
      >
        <EntryIcon icon={toolConfig.icon} color={toolConfig.color} />
        <div className="flex flex-col min-w-0">
          <span className="text-[12px] text-white truncate">{toolConfig.name}</span>
          <span className="text-[11px] text-text-muted truncate">{toolConfig.description}</span>
        </div>
        {isAdded && <span className="ml-auto text-[10px] text-text-muted shrink-0">added</span>}
      </button>
    )
  }

  return (
    <div className="flex flex-col" onClick={(e) => e.stopPropagation()}>
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
        <Search className="w-3.5 h-3.5 text-text-muted shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search tools..."
          className="flex-1 bg-transparent text-[12px] text-white placeholder:text-text-muted outline-none"
        />
      </div>

      <div className="max-h-[280px] overflow-y-auto py-1">
        {!query && (
          <>
            <button
              onClick={() => setView('create')}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-surface-5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5 shrink-0 text-text-muted" />
              <span className="text-[12px] font-semibold text-white">Create Tool</span>
            </button>
            <button
              onClick={() => setView('mcp')}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-surface-5 transition-colors"
            >
              <Server className="w-3.5 h-3.5 shrink-0 text-text-muted" />
              <span className="text-[12px] font-semibold text-white">Add MCP Server</span>
            </button>
            <div className="mx-3 my-1 border-t border-border" />
          </>
        )}

        {filteredBuiltin.length > 0 && (
          <>
            <div className="px-3 pt-2 pb-1 text-[10px] font-bold text-text-muted uppercase tracking-wider">
              Built-in Tools
            </div>
            {filteredBuiltin.map((t) => renderToolBtn(t))}
          </>
        )}

        {filteredIntegrations.length > 0 && (
          <>
            <div className="px-3 pt-2 pb-1 text-[10px] font-bold text-text-muted uppercase tracking-wider">
              Integrations
            </div>
            {filteredIntegrations.map((t) => renderToolBtn(t))}
          </>
        )}

        {!hasResults && query && (
          <div className="px-3 py-4 text-center text-[12px] text-text-muted">
            No tools match &ldquo;{query}&rdquo;
          </div>
        )}

        {!hasResults && !query && (
          <div className="px-3 py-4 text-center text-[12px] text-text-muted">
            No tools available
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ToolSelectorField — main export
// ---------------------------------------------------------------------------

export interface ToolSelectorFieldProps {
  value: SelectedTool[]
  onChange: (tools: SelectedTool[]) => void
  disabled?: boolean
}

export const ToolSelectorField: React.FC<ToolSelectorFieldProps> = ({
  value = [],
  onChange,
  disabled = false,
}) => {
  const [comboboxOpen, setComboboxOpen] = useState(false)
  const comboboxRef = useRef<HTMLDivElement>(null)
  const { builtinTools, integrations, toolsById } = useAvailableTools()

  useEffect(() => {
    if (!comboboxOpen) return
    const handler = (e: MouseEvent) => {
      if (comboboxRef.current && !comboboxRef.current.contains(e.target as Node)) {
        setComboboxOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [comboboxOpen])

  const selectedToolIds = new Set(
    value.filter((t) => t.kind === 'tool' && t.toolId).map((t) => t.toolId!),
  )

  const handleAdd = (entry: SelectedTool) => onChange([...value, entry])

  const handleAddTool = (toolConfig: ToolConfig) =>
    handleAdd({ kind: 'tool', toolId: toolConfig.id, title: toolConfig.name, params: {}, isExpanded: true, usageControl: 'auto' })

  const handleAddSkill = (skill: Skill) =>
    handleAdd({
      kind: 'skill',
      toolId: skill.id,
      title: skill.name,
      icon: skill.icon,
      color: skill.color,
      params: {},
      usageControl: 'auto',
    })

  const handleRemove = (index: number) => onChange(value.filter((_, i) => i !== index))

  const handleToggleExpand = (index: number) =>
    onChange(value.map((t, i) => (i === index ? { ...t, isExpanded: !t.isExpanded } : t)))

  const handleParamChange = (index: number, key: string, val: unknown) =>
    onChange(value.map((t, i) => (i === index ? { ...t, params: { ...t.params, [key]: val } } : t)))

  const handleUsageControlChange = (index: number, usageControl: UsageControl) =>
    onChange(value.map((t, i) => (i === index ? { ...t, usageControl } : t)))

  const handleMcpUpdate = (index: number, updates: Partial<SelectedTool>) =>
    onChange(value.map((t, i) => (i === index ? { ...t, ...updates } : t)))

  return (
    <div className={cn('flex flex-col gap-2', disabled && 'opacity-50 pointer-events-none')}>
      {value.length > 0 && (
        <div className="flex flex-col gap-1.5">
          {value.map((tool, index) => {
            if (tool.kind === 'mcp') {
              return (
                <McpServerCard
                  key={`mcp-${tool.mcpName ?? index}`}
                  tool={tool}
                  onRemove={() => handleRemove(index)}
                  onUpdate={(updates) => handleMcpUpdate(index, updates)}
                />
              )
            }
            if (tool.kind === 'skill') {
              return (
                <SkillCard
                  key={`skill-${tool.toolId ?? index}`}
                  tool={tool}
                  onRemove={() => handleRemove(index)}
                />
              )
            }
            return (
              <ToolCard
                key={`tool-${tool.toolId ?? index}`}
                tool={tool}
                toolConfig={tool.toolId ? toolsById[tool.toolId] : undefined}
                onRemove={() => handleRemove(index)}
                onToggleExpand={() => handleToggleExpand(index)}
                onParamChange={(key, val) => handleParamChange(index, key, val)}
                onUsageControlChange={(uc) => handleUsageControlChange(index, uc)}
              />
            )
          })}
        </div>
      )}

      <div className="relative" ref={comboboxRef}>
        <button
          onClick={() => setComboboxOpen((v) => !v)}
          className={cn(
            'w-full flex items-center gap-2 border rounded-md px-3 h-[36px] text-[13px] transition-colors',
            value.length === 0
              ? 'border-dashed border-border hover:border-border-strong bg-transparent text-text-muted hover:text-white'
              : 'border-border bg-surface-editor text-text-muted hover:text-white hover:border-border-strong',
          )}
        >
          <Plus className="w-3.5 h-3.5 shrink-0" />
          <span>Add tool...</span>
        </button>

        {comboboxOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-surface-modal border border-border rounded-md shadow-lg z-50 overflow-hidden">
            <ToolCombobox
              builtinTools={builtinTools}
              integrations={integrations}
              selectedToolIds={selectedToolIds}
              onSelectTool={handleAddTool}
              onAddMcp={handleAdd}
              onAddSkill={handleAddSkill}
              onClose={() => setComboboxOpen(false)}
            />
          </div>
        )}
      </div>
    </div>
  )
}
