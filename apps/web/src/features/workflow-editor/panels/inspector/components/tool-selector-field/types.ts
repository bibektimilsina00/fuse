export type ToolEntryKind = 'tool' | 'mcp' | 'skill'

export interface SelectedTool {
  kind?: ToolEntryKind            // defaults to 'tool' for backward compat
  // Registry tool fields (kind='tool')
  toolId?: string                 // e.g. 'slack_send_message'
  title: string                   // display name
  icon?: string
  color?: string
  params: Record<string, unknown> // user-provided param values
  isExpanded?: boolean
  usageControl?: 'auto' | 'force' | 'none'
  // MCP server fields (kind='mcp')
  mcpName?: string
  mcpUrl?: string
  mcpApiKey?: string
}
