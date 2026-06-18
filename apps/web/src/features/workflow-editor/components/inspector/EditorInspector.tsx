import { SlidersHorizontal } from 'lucide-react'
import type { Node } from 'reactflow'
import { Empty } from '@/shared/components'
import { cn } from '@/lib/cn'
import { useInspectorNode } from './hooks/use-inspector-node'
import { InspectorHeader } from './components/inspector-header'
import { PropertyGroupList } from './components/property-group-list'
import { TriggerFixtureChip } from './components/trigger-fixture-chip'
import { UpstreamConnectionsSection } from './components/upstream-connections-section'

interface EditorInspectorProps {
  nodes: Node[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  className?: string
}

export function EditorInspector({ nodes, updateNodeData, className }: EditorInspectorProps) {
  const {
    selectedNode,
    definition,
    properties,
    basicGroups,
    advancedGroups,
    showAdvanced,
    toggleAdvanced,
    updateProperty,
    updateProperties,
    updateLabel,
  } = useInspectorNode({ nodes, updateNodeData })

  return (
    <aside
      className={cn(
        'flex h-full w-full flex-col overflow-hidden bg-[var(--bg-2)]',
        className,
      )}
    >
      {!selectedNode || !definition ? (
        <Empty
          icon={<SlidersHorizontal />}
          title="No node selected"
          description="Select a workflow node to edit its dynamic properties."
          className="h-full"
        />
      ) : (
        <>
          <InspectorHeader
            label={(selectedNode.data?.label as string | undefined) || definition.name}
            definition={definition}
            onLabelChange={updateLabel}
          />

          {definition.category === 'trigger' && (
            <TriggerFixtureChip nodeId={selectedNode.id} />
          )}

          {/* Scrollable body */}
          <div className="min-h-0 flex-1 overflow-y-auto">
            {basicGroups.length === 0 && advancedGroups.length === 0 ? (
              <Empty
                title="No configurable fields"
                description="This node does not expose editable properties."
                className="h-full"
              />
            ) : (
              <div className="flex flex-col gap-[16px] p-4 pb-6">
                <div className="flex items-center justify-between gap-4 h-8">
                  <div className="text-[10.5px] font-bold tracking-[0.08em] text-[var(--text-dim)] uppercase">
                    Configuration
                  </div>
                  {advancedGroups.length > 0 && (
                    <div className="flex p-0.5 rounded-[7px] bg-[var(--bg)] border border-[var(--border-soft)]">
                      <button
                        type="button"
                        onClick={() => { if (showAdvanced) toggleAdvanced() }}
                        className={cn(
                          "px-3 py-1 text-[11px] font-semibold rounded-[5px] transition-all duration-[120ms]",
                          !showAdvanced
                            ? "bg-[var(--surface)] text-[var(--text)] border border-[var(--border-soft)] shadow-[var(--shadow-float)]"
                            : "text-[var(--text-mute)] hover:text-[var(--text)] border border-transparent"
                        )}
                      >
                        Basic
                      </button>
                      <button
                        type="button"
                        onClick={() => { if (!showAdvanced) toggleAdvanced() }}
                        className={cn(
                          "px-3 py-1 text-[11px] font-semibold rounded-[5px] transition-all duration-[120ms]",
                          showAdvanced
                            ? "bg-[var(--surface)] text-[var(--text)] border border-[var(--border-soft)] shadow-[var(--shadow-float)]"
                            : "text-[var(--text-mute)] hover:text-[var(--text)] border border-transparent"
                        )}
                      >
                        Advanced
                      </button>
                    </div>
                  )}
                </div>

                {!showAdvanced ? (
                  <PropertyGroupList
                    groups={basicGroups}
                    definition={definition}
                    properties={properties}
                    onPropertyChange={updateProperty}
                    onPropertiesChange={updateProperties}
                  />
                ) : (
                  <PropertyGroupList
                    groups={advancedGroups}
                    definition={definition}
                    properties={properties}
                    onPropertyChange={updateProperty}
                    onPropertiesChange={updateProperties}
                  />
                )}
              </div>
            )}
          </div>

          <UpstreamConnectionsSection nodeId={selectedNode.id} />
        </>
      )}
    </aside>
  )
}
