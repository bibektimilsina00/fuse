import { z } from 'zod'
import type { Node, Edge } from 'reactflow'

// ── Workflow graph ────────────────────────────────────────────────────────────

export interface WorkflowGraph {
  nodes: Node[]
  edges: Edge[]
}

// ── Workflow (from backend) ───────────────────────────────────────────────────

export const WorkflowDetailSchema = z.object({
  id:             z.string().uuid(),
  name:           z.string(),
  description:    z.string().nullable().optional(),
  is_active:      z.boolean(),
  color:          z.string().nullable().optional(),
  graph:          z.any(),
  version_vector: z.number().default(0),
  created_at:     z.string(),
  updated_at:     z.string(),
})
export type WorkflowDetail = z.infer<typeof WorkflowDetailSchema>

// ── Save state ────────────────────────────────────────────────────────────────

export type SaveState = 'saved' | 'saving' | 'unsaved' | 'error'
