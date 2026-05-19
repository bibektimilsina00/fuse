import {
  slackTool,
  slackSendMessageTool,
  slackUpdateMessageTool,
  slackDeleteMessageTool,
  slackListChannelsTool,
  slackGetChannelInfoTool,
} from './slack'
import { httpRequestTool } from './http'
import type { ToolConfig } from './types'

export const allTools: Record<string, ToolConfig> = {
  slack: slackTool,
  slack_send_message: slackSendMessageTool,
  slack_update_message: slackUpdateMessageTool,
  slack_delete_message: slackDeleteMessageTool,
  slack_list_channels: slackListChannelsTool,
  slack_get_channel_info: slackGetChannelInfoTool,
  http_request: httpRequestTool,
}

export function getTool(id: string): ToolConfig | undefined {
  return allTools[id]
}

export function getToolsByCategory(category: 'builtin' | 'integration'): ToolConfig[] {
  return Object.values(allTools).filter((t) => t.category === category)
}

function stripVersionSuffix(id: string): string {
  return id.replace(/_v\d+$/, '')
}

export function resolveToolId(name: string): string {
  if (allTools[name]) return name
  // Find latest version matching base name
  const base = stripVersionSuffix(name)
  const matches = Object.keys(allTools).filter((id) => stripVersionSuffix(id) === base)
  if (matches.length === 0) return name
  return matches.sort((a, b) => {
    const va = parseInt(a.match(/_v(\d+)$/)?.[1] ?? '1', 10)
    const vb = parseInt(b.match(/_v(\d+)$/)?.[1] ?? '1', 10)
    return vb - va
  })[0]
}
