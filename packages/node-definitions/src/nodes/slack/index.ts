import type { NodeDefinition } from '../../types'

export const SlackNodeDefinition: NodeDefinition = {
  type: 'action.slack',
  name: 'Slack',
  category: 'action',
  description: 'Send messages or interact with Slack channels.',
  icon: 'MessageSquare',
  color: '#4a154b',
  inputs: 1,
  outputs: 1,
  credentialType: 'slack_oauth',
  properties: [
    {
      name: 'action',
      label: 'Action',
      type: 'options',
      default: 'chat.postMessage',
      options: [
        { label: 'Send Message', value: 'chat.postMessage' },
      ],
    },
    { name: 'channel', label: 'Channel ID', type: 'string', required: true },
    { name: 'text', label: 'Message Text', type: 'string', required: true },
  ],
  allowError: true,
}

export const SlackTriggerDefinition: NodeDefinition = {
  type: 'trigger.slack',
  name: 'Slack Trigger',
  category: 'trigger',
  description: 'Wait for Slack events to start the workflow.',
  icon: 'Zap',
  color: '#4a154b',
  inputs: 0,
  outputs: 1,
  credentialType: 'slack_oauth',
  properties: [
    {
      name: 'event',
      label: 'Event Type',
      type: 'options',
      default: 'message',
      options: [
        { label: 'On Message', value: 'message' },
      ],
    },
  ],
}
