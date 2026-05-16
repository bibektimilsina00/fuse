import type { NodeDefinition } from '../../types'

export const MergeDefinition: NodeDefinition = {
  type: 'logic.merge',
  name: 'Merge',
  category: 'logic',
  description: 'Merge multiple inputs into one output',
  icon: 'Merge',
  color: '#8b5cf6',
  inputs: 2,
  outputs: 1,
  properties: [
    {
      name: 'mode',
      label: 'Merge Mode',
      type: 'options',
      default: 'shallow',
      options: [
        { label: 'Shallow merge', value: 'shallow' },
        { label: 'Deep merge', value: 'deep' },
      ],
    },
  ],
}
