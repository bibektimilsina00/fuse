import type { ToolConfig } from '../types'

const SLACK_CREDENTIAL: import('../../types').NodeProperty = {
  name: 'credential',
  label: 'Slack Account',
  type: 'credential',
  required: true,
  credentialType: 'slack_oauth',
  visibility: 'user-only',
}

// Channel with basic (dropdown) / advanced (ID input) canonical pair
const CHANNEL_DROPDOWN: import('../../types').NodeProperty = {
  name: 'channel',
  label: 'Channel',
  type: 'options',
  required: true,
  loadOptions: '/integrations/slack/channels',
  loadOptionsDependsOn: ['credential'],
  mode: 'basic',
  canonicalId: 'channel',
  description: 'Select a channel from the dropdown.',
}

const CHANNEL_ID_INPUT: import('../../types').NodeProperty = {
  name: 'channelId',
  label: 'Channel ID',
  type: 'string',
  required: true,
  placeholder: 'C1234567890',
  mode: 'advanced',
  canonicalId: 'channel',
  description: 'Enter the channel ID directly.',
}

const SLACK_OPERATION: import('../../types').NodeProperty = {
  name: 'operation',
  label: 'Operation',
  type: 'options',
  default: 'send_message',
  options: [
    { label: 'Send Message', value: 'send_message' },
    { label: 'Update Message', value: 'update_message' },
    { label: 'Delete Message', value: 'delete_message' },
    { label: 'List Channels', value: 'list_channels' },
    { label: 'Get Channel Info', value: 'get_channel_info' },
  ],
  visibility: 'user-only',
}

const CHANNEL_REQUIRED_FOR_MESSAGE_OPS = {
  field: 'operation',
  value: ['send_message', 'update_message', 'delete_message', 'get_channel_info'],
}

export const slackTool: ToolConfig = {
  id: 'slack',
  name: 'Slack',
  description: 'Let the agent use selected Slack operations',
  category: 'integration',
  icon: 'MessageSquare',
  color: '#4a154b',
  sourceNodeType: 'action.slack',
  credentialType: 'slack_oauth',
  oauth: { required: true, credentialType: 'slack_oauth' },
  properties: [
    SLACK_CREDENTIAL,
    SLACK_OPERATION,
    { ...CHANNEL_DROPDOWN, condition: CHANNEL_REQUIRED_FOR_MESSAGE_OPS },
    { ...CHANNEL_ID_INPUT, condition: CHANNEL_REQUIRED_FOR_MESSAGE_OPS },
    {
      name: 'text',
      label: 'Message',
      type: 'string',
      required: true,
      placeholder: 'Hello, world!',
      description: 'The message text to send.',
      condition: { field: 'operation', value: ['send_message', 'update_message'] },
    },
    {
      name: 'ts',
      label: 'Message Timestamp',
      type: 'string',
      required: true,
      placeholder: '1234567890.123456',
      description: 'Timestamp of the message to update or delete.',
      condition: { field: 'operation', value: ['update_message', 'delete_message'] },
    },
    {
      name: 'thread_ts',
      label: 'Reply to thread',
      type: 'string',
      placeholder: '1234567890.123456',
      description: 'Timestamp of the message to reply to.',
      condition: { field: 'operation', value: 'send_message' },
    },
    {
      name: 'blocks',
      label: 'Block Kit',
      type: 'json',
      description: 'Optional Block Kit blocks JSON array.',
      visibility: 'user-only',
      condition: { field: 'operation', value: ['send_message', 'update_message'] },
    },
    {
      name: 'limit',
      label: 'Limit',
      type: 'number',
      default: 100,
      visibility: 'user-only',
      description: 'Maximum number of channels to return.',
      condition: { field: 'operation', value: 'list_channels' },
    },
  ],
}

export const slackSendMessageTool: ToolConfig = {
  id: 'slack_send_message',
  name: 'Send Message',
  description: 'Send a message to a Slack channel',
  category: 'integration',
  icon: 'MessageSquare',
  color: '#4a154b',
  credentialType: 'slack_oauth',
  oauth: { required: true, credentialType: 'slack_oauth' },
  properties: [
    SLACK_CREDENTIAL,
    CHANNEL_DROPDOWN,
    CHANNEL_ID_INPUT,
    {
      name: 'text',
      label: 'Message',
      type: 'string',
      required: true,
      placeholder: 'Hello, world!',
      description: 'The message text to send.',
    },
    {
      name: 'thread_ts',
      label: 'Reply to thread',
      type: 'string',
      placeholder: '1234567890.123456',
      description: 'Timestamp of the message to reply to.',
    },
    {
      name: 'blocks',
      label: 'Block Kit',
      type: 'json',
      description: 'Optional Block Kit blocks JSON array.',
      visibility: 'user-only',
    },
  ],
}

export const slackUpdateMessageTool: ToolConfig = {
  id: 'slack_update_message',
  name: 'Update Message',
  description: 'Update an existing message in a Slack channel',
  category: 'integration',
  icon: 'MessageSquare',
  color: '#4a154b',
  credentialType: 'slack_oauth',
  oauth: { required: true, credentialType: 'slack_oauth' },
  properties: [
    SLACK_CREDENTIAL,
    CHANNEL_DROPDOWN,
    CHANNEL_ID_INPUT,
    {
      name: 'ts',
      label: 'Message Timestamp',
      type: 'string',
      required: true,
      placeholder: '1234567890.123456',
      description: 'Timestamp of the message to update.',
    },
    {
      name: 'text',
      label: 'New Message',
      type: 'string',
      placeholder: 'Updated text',
    },
    {
      name: 'blocks',
      label: 'Block Kit',
      type: 'json',
      visibility: 'user-only',
    },
  ],
}

export const slackDeleteMessageTool: ToolConfig = {
  id: 'slack_delete_message',
  name: 'Delete Message',
  description: 'Delete a message from a Slack channel',
  category: 'integration',
  icon: 'MessageSquare',
  color: '#4a154b',
  credentialType: 'slack_oauth',
  oauth: { required: true, credentialType: 'slack_oauth' },
  properties: [
    SLACK_CREDENTIAL,
    CHANNEL_DROPDOWN,
    CHANNEL_ID_INPUT,
    {
      name: 'ts',
      label: 'Message Timestamp',
      type: 'string',
      required: true,
      placeholder: '1234567890.123456',
      description: 'Timestamp of the message to delete.',
    },
  ],
}

export const slackListChannelsTool: ToolConfig = {
  id: 'slack_list_channels',
  name: 'List Channels',
  description: 'List all channels in a Slack workspace',
  category: 'integration',
  icon: 'MessageSquare',
  color: '#4a154b',
  credentialType: 'slack_oauth',
  oauth: { required: true, credentialType: 'slack_oauth' },
  properties: [
    SLACK_CREDENTIAL,
    {
      name: 'limit',
      label: 'Limit',
      type: 'number',
      default: 100,
      visibility: 'user-only',
      description: 'Maximum number of channels to return.',
    },
  ],
}

export const slackGetChannelInfoTool: ToolConfig = {
  id: 'slack_get_channel_info',
  name: 'Get Channel Info',
  description: 'Get information about a Slack channel',
  category: 'integration',
  icon: 'MessageSquare',
  color: '#4a154b',
  credentialType: 'slack_oauth',
  oauth: { required: true, credentialType: 'slack_oauth' },
  properties: [
    SLACK_CREDENTIAL,
    CHANNEL_DROPDOWN,
    CHANNEL_ID_INPUT,
  ],
}
