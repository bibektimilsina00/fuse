import React, { useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useNodeAncestors } from '@/features/workflow-editor/hooks/use-node-ancestors'
import { useEditorLayout } from './hooks/use-editor-layout'
import { ConnectionsPanel } from './components/connections-panel'
import { InterpolationPicker } from './components/interpolation-picker'
import { PropertyGroupList } from './components/PropertyGroupList'
import type { CanonicalModeOverrides } from './visibility'

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="flex-1 flex items-center justify-center p-8 text-center">
    <span className="text-[14px] text-text-muted font-medium leading-relaxed">{message}</span>
  </div>
)

// ─── EditorTab ────────────────────────────────────────────────────────────────

export const EditorTab: React.FC = () => {
  const { nodes, edges, selectedNodeId, nodeSelectionTimestamp, updateNodeData, nodeDefinitions } = useWorkflowStore()
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [usedFields, setUsedFields] = useState<Set<string>>(new Set())
  const [picker, setPicker] = useState<{ rect: DOMRect; onSelect: (val: string) => void } | null>(null)

  useEffect(() => {
    setUsedFields(new Set())
    setPicker(null)
  }, [selectedNodeId, nodeSelectionTimestamp])

  const selectedNode = nodes.find(n => n.id === selectedNodeId)
  const definition = selectedNode ? nodeDefinitions.find(d => d.type === selectedNode.type) : null
  const properties: Record<string, any> = selectedNode?.data?.properties || {}
  const canonicalModes: CanonicalModeOverrides = selectedNode?.data?.canonicalModes || {}

  const connectedNodes = useNodeAncestors(selectedNodeId, nodes, edges)
  const { mainGroups, advancedProps, hasAdvanced, canonicalIndex } = useEditorLayout(
    definition,
    properties,
    canonicalModes,
  )

  if (!selectedNode) return <EmptyState message="Select a node on the canvas to configure its properties" />
  if (!definition) return <EmptyState message={`Metadata not available for: ${selectedNode.type}`} />

  const handlePropertyChange = (name: string, value: any) => {
    updateNodeData(selectedNode.id, {
      properties: { ...(selectedNode.data?.properties || {}), [name]: value },
    })
  }

  const toggleCanonicalMode = (canonicalId: string, currentMode: 'basic' | 'advanced') => {
    const next: 'basic' | 'advanced' = currentMode === 'basic' ? 'advanced' : 'basic'
    updateNodeData(selectedNode.id, {
      canonicalModes: { ...canonicalModes, [canonicalId]: next },
    })
  }

  const isEmpty = mainGroups.every(g => g.props.length === 0) && !hasAdvanced

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[var(--bg)] relative">
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 pb-10">
        {isEmpty && (
          <p className="py-8 text-center text-[13px] text-[var(--text-muted)]">
            This node has no configurable properties.
          </p>
        )}

        <PropertyGroupList
          groups={mainGroups}
          selectedNode={selectedNode}
          definition={definition}
          properties={properties}
          canonicalIndex={canonicalIndex}
          canonicalModes={canonicalModes}
          onPropertyChange={handlePropertyChange}
          onShowPicker={(rect, onSelect) => setPicker({ rect, onSelect })}
          isFirstClickAllowed={(subId) => !usedFields.has(subId || '')}
          onFirstClickUsed={(subId) => setUsedFields(prev => new Set(prev).add(subId || ''))}
          onCanonicalToggle={toggleCanonicalMode}
        />

        {hasAdvanced && (
          <div className="mt-8 flex flex-col">
            <div
              onClick={() => setShowAdvanced(v => !v)}
              className="flex items-center justify-center gap-3 cursor-pointer group mb-2"
            >
              <div className="flex-1 h-[1px] border-b border-dashed border-border" />
              <span className="text-[12px] font-bold text-white flex items-center gap-1.5 hover:text-[var(--text-muted)] transition-colors">
                Show additional fields
                <ChevronDown className={cn("w-3.5 h-3.5 transition-transform duration-200", showAdvanced && "rotate-180")} />
              </span>
              <div className="flex-1 h-[1px] border-b border-dashed border-border" />
            </div>

            {showAdvanced && (
              <div className="flex flex-col mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <PropertyGroupList
                  groups={[{ group: null, props: advancedProps }]}
                  selectedNode={selectedNode}
                  definition={definition}
                  properties={properties}
                  canonicalIndex={canonicalIndex}
                  canonicalModes={canonicalModes}
                  onPropertyChange={handlePropertyChange}
                  onShowPicker={(rect, onSelect) => setPicker({ rect, onSelect })}
                  isFirstClickAllowed={(subId) => !usedFields.has(subId || '')}
                  onFirstClickUsed={(subId) => setUsedFields(prev => new Set(prev).add(subId || ''))}
                  onCanonicalToggle={toggleCanonicalMode}
                />
              </div>
            )}
          </div>
        )}
      </div>

      <ConnectionsPanel connectedNodes={connectedNodes} />

      {picker && (
        <InterpolationPicker
          anchorRect={picker.rect}
          onSelect={(val) => { picker.onSelect(val); setPicker(null) }}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  )
}
