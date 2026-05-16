import type { NodeDefinition } from '../../types'

export const SetVariableDefinition: NodeDefinition = {
  type: 'logic.set_variable',
  name: 'Set Variable',
  category: 'logic',
  description: 'Store a value in workflow variables for use by downstream nodes',
  icon: 'Variable',
  color: '#ec4899',
  inputs: 1,
  outputs: 1,
  properties: [
    {
      name: 'key',
      label: 'Variable Name',
      type: 'string',
      required: true,
      placeholder: 'myVariable',
    },
    {
      name: 'value',
      label: 'Value',
      type: 'string',
      required: true,
      placeholder: 'Enter value or use {{ interpolation }}',
    },
  ],
}
