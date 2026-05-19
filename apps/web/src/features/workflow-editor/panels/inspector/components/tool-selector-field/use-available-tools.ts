import { useMemo } from 'react'
import { getToolsByCategory } from '@fuse/node-definitions'
import { useWorkflowStore } from '@/stores/workflow-store'
import type { ToolConfig } from '@fuse/node-definitions'

export interface AvailableTools {
  builtinTools: ToolConfig[]
  integrations: ToolConfig[]
  toolsById: Record<string, ToolConfig>
  operationToolMap: Record<string, string>
}

const TOOL_CATEGORIES = new Set(['action', 'integration'])

export function useAvailableTools(): AvailableTools {
  // nodeDefinitions comes from the API via useNodes() — contains tools[] from Python NodeMetadata
  const nodeDefinitions = useWorkflowStore((s) => s.nodeDefinitions)

  return useMemo(() => {
    const availableToolIds = new Set<string>()
    const operationToolMap: Record<string, string> = {}
    const nodesByType = new Map(nodeDefinitions.map((def) => [def.type, def]))

    for (const def of nodeDefinitions) {
      if (!def.tools || !TOOL_CATEGORIES.has(def.category)) continue
      for (const toolId of def.tools) {
        availableToolIds.add(toolId)
      }
      if (def.operationToolMap) {
        Object.assign(operationToolMap, def.operationToolMap)
      }
    }

    const deriveToolConfig = (tool: ToolConfig): ToolConfig => {
      if (!tool.sourceNodeType) return tool
      const sourceNode = nodesByType.get(tool.sourceNodeType)
      if (!sourceNode) return tool
      return {
        ...tool,
        description: sourceNode.description || tool.description,
        credentialType: sourceNode.credentialType ?? tool.credentialType,
        properties: sourceNode.properties,
      }
    }

    const allBuiltinTools = getToolsByCategory('builtin').map(deriveToolConfig)
    const allIntegrationTools = getToolsByCategory('integration').map(deriveToolConfig)

    const builtinTools = allBuiltinTools.filter((tool) => availableToolIds.has(tool.id))
    const integrations = allIntegrationTools.filter((tool) => availableToolIds.has(tool.id))

    const toolsById = Object.fromEntries(
      [...allBuiltinTools, ...allIntegrationTools].map((tool) => [tool.id, tool]),
    )

    return {
      builtinTools,
      integrations,
      toolsById,
      operationToolMap,
    }
  }, [nodeDefinitions])
}
