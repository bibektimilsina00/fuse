import type { NodeDefinition } from '../../types'

export const JsonTransformDefinition: NodeDefinition = {
  type: 'logic.json_transform',
  name: 'JSON Transform',
  category: 'logic',
  description: 'Reshape input data using a JSON template (supports Jinja2)',
  icon: 'FileJson',
  color: '#3b82f6',
  inputs: 1,
  outputs: 1,
  properties: [
    {
      name: 'template',
      label: 'Output Template (JSON)',
      type: 'json',
      required: true,
      placeholder: '{"name": "{{ input.name }}", "email": "{{ input.email }}"}',
    },
  ],
}
