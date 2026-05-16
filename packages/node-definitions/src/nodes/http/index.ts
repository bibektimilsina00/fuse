import type { NodeDefinition } from '../../types'

export const HttpRequestDefinition: NodeDefinition = {
  type: 'action.http_request',
  name: 'HTTP Request',
  category: 'action',
  description: 'Make HTTP requests with comprehensive support for methods, headers, query parameters, path parameters, and form data.',
  icon: 'Globe',
  color: '#3b82f6',
  inputs: 1,
  outputs: 1,
  properties: [
    { name: 'url', label: 'URL', type: 'string', required: true },
    {
      name: 'method',
      label: 'Method',
      type: 'options',
      default: 'GET',
      options: [
        { label: 'GET', value: 'GET' },
        { label: 'POST', value: 'POST' },
        { label: 'PUT', value: 'PUT' },
        { label: 'DELETE', value: 'DELETE' },
        { label: 'PATCH', value: 'PATCH' },
      ],
    },
    { name: 'headers', label: 'Headers', type: 'key-value', required: false },
    { name: 'params', label: 'Query Parameters', type: 'key-value', required: false },
    { name: 'body', label: 'Body', type: 'json', required: false },
    { name: 'timeout', label: 'Timeout (ms)', type: 'number', default: 30000 },
  ],
  allowError: true,
}

export const WebhookTriggerDefinition: NodeDefinition = {
  type: 'trigger.webhook',
  name: 'Webhook',
  category: 'trigger',
  description: 'Wait for an incoming HTTP request to start the workflow.',
  icon: 'Zap',
  color: '#10b981',
  inputs: 0,
  outputs: 1,
  properties: [
    { name: 'path', label: 'Webhook Path', type: 'string', required: true, placeholder: 'my-webhook' },
    {
      name: 'method',
      label: 'Method',
      type: 'options',
      default: 'POST',
      options: [
        { label: 'GET', value: 'GET' },
        { label: 'POST', value: 'POST' },
      ],
    },
  ],
}
