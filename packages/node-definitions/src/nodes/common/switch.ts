import type { NodeDefinition } from '../../types'

export const SwitchDefinition: NodeDefinition = {
  type: 'logic.switch',
  name: 'Switch',
  category: 'logic',
  description: 'Route to different branches based on a value',
  icon: 'Split',
  color: '#f59e0b',
  inputs: 1,
  outputs: 2,
  properties: [
    {
      name: 'field',
      label: 'Field to Check',
      type: 'string',
      required: true,
      placeholder: 'status',
    },
    {
      name: 'cases',
      label: 'Cases',
      type: 'json',
      required: false,
      placeholder: '[{"value":"success","label":"Success"},{"value":"error","label":"Error"}]',
    },
  ],
}
