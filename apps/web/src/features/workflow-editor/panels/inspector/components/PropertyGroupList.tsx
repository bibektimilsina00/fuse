import React from 'react'
import type { NodeDefinition, NodeProperty } from '@fuse/node-definitions'
import { PropertyField } from './property-field/PropertyField'
import type { CanonicalIndex, CanonicalModeOverrides } from '../visibility'
import { isCanonicalPair, resolveCanonicalMode } from '../visibility'
import type { PropertyGroup } from '../hooks/use-editor-layout'

export const SectionHeader: React.FC<{ label: string }> = ({ label }) => (
  <div className="mb-3 mt-6 pb-1 border-b border-border">
    <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">{label}</span>
  </div>
)

export const FieldDivider = () => <div className="border-t border-dashed border-border my-4" />

interface PropertyGroupListProps {
  groups: PropertyGroup[]
  selectedNode: any
  definition: NodeDefinition | any
  properties: Record<string, any>
  canonicalIndex: CanonicalIndex
  canonicalModes: CanonicalModeOverrides
  onPropertyChange: (name: string, value: any) => void
  onShowPicker?: (rect: DOMRect, onSelect: (val: string) => void) => void
  isFirstClickAllowed?: (subId?: string) => boolean
  onFirstClickUsed?: (subId?: string) => void
  onCanonicalToggle?: (canonicalId: string, current: 'basic' | 'advanced') => void
}

export const PropertyGroupList: React.FC<PropertyGroupListProps> = ({
  groups,
  selectedNode,
  definition,
  properties,
  canonicalIndex,
  canonicalModes,
  onPropertyChange,
  onShowPicker = () => {},
  isFirstClickAllowed = () => true,
  onFirstClickUsed = () => {},
  onCanonicalToggle,
}) => {
  const buildCanonicalToggle = (prop: NodeProperty) => {
    const canonicalId = canonicalIndex.canonicalIdByPropName[prop.name]
    if (!canonicalId) return undefined
    const group = canonicalIndex.groupsById[canonicalId]
    if (!isCanonicalPair(group)) return undefined
    const mode = resolveCanonicalMode(group, properties, canonicalModes)
    return {
      mode,
      onToggle: () => onCanonicalToggle?.(canonicalId, mode),
    }
  }

  return (
    <>
      {groups.map((group, gi) => (
        <div key={group.group ?? gi}>
          {group.group && <SectionHeader label={group.group} />}
          {group.props.map((prop, i) => (
            <React.Fragment key={prop.name}>
              {(i > 0 || (!group.group && gi > 0)) && <FieldDivider />}
              <PropertyField
                prop={prop}
                selectedNode={selectedNode}
                properties={properties}
                handlePropertyChange={onPropertyChange}
                onShowPicker={onShowPicker}
                isFirstClickAllowed={isFirstClickAllowed}
                onFirstClickUsed={onFirstClickUsed}
                definition={definition}
                canonicalIndex={canonicalIndex}
                canonicalModes={canonicalModes}
                canonicalToggle={buildCanonicalToggle(prop)}
              />
            </React.Fragment>
          ))}
        </div>
      ))}
    </>
  )
}
