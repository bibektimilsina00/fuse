import type { NodeSchema } from './node';
import type { EdgeSchema } from './edge';

export interface WorkflowSchema {
  id: string;
  name: string;
  description?: string;
  nodes: NodeSchema[];
  edges: EdgeSchema[];
  metadata?: Record<string, any>;
}
