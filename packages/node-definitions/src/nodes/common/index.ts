export * from './set_variable'
export * from './json_transform'
export * from './merge'
export * from './switch'

// Existing common nodes (scaffolded for consistency)
export const ManualTriggerDefinition = {
  type: 'trigger.manual',
  name: 'Start',
  category: 'trigger',
  description: 'Start the workflow manually.',
  icon: 'Play',
  color: '#10b981',
  inputs: 0,
  outputs: 1,
  properties: [],
}

export const ConditionDefinition = {
  type: 'logic.condition',
  name: 'Condition',
  category: 'logic',
  description: 'Route based on a boolean condition.',
  icon: 'Split',
  color: '#f59e0b',
  inputs: 1,
  outputs: 2,
  properties: [
    { name: 'condition', label: 'Condition', type: 'string', required: true },
  ],
}

export const DelayDefinition = {
  type: 'logic.delay',
  name: 'Delay',
  category: 'logic',
  description: 'Wait for a specified duration.',
  icon: 'Clock',
  color: '#6366f1',
  inputs: 1,
  outputs: 1,
  properties: [
    { name: 'seconds', label: 'Seconds', type: 'number', required: true, default: 5 },
  ],
}
