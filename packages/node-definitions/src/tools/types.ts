import type { NodeProperty } from '../types'

export type ToolParamVisibility = 'user-or-llm' | 'user-only' | 'llm-only' | 'hidden'

export interface ToolOAuth {
  required: boolean
  credentialType: string
}

export interface ToolRetryConfig {
  enabled: boolean
  maxRetries?: number
  initialDelayMs?: number
  maxDelayMs?: number
}

export interface ToolConfig {
  id: string
  name: string
  description: string
  category: 'builtin' | 'integration'
  icon: string
  color: string
  sourceNodeType?: string
  credentialType?: string       // top-level credential — injected automatically at runtime
  properties: NodeProperty[]    // full NodeProperty[] — same type as NodeDefinition.properties
  outputs?: Record<string, { type: string; description?: string }>
  oauth?: ToolOAuth             // kept for backend execution (OAuth token injection)
  retry?: ToolRetryConfig
}

// Re-export for callers that used ToolParam previously
export type { NodeProperty as ToolParam }
