export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type ExecutionEventType = 
  | 'execution_started' 
  | 'execution_completed' 
  | 'execution_failed' 
  | 'node_started' 
  | 'node_completed' 
  | 'node_failed'
  | 'log_synced';

export interface ExecutionEvent {
  type: ExecutionEventType;
  id?: string;
  execution_id: string;
  timestamp: string;
  node_id?: string;
  node_type?: string;
  label?: string;
  level?: string;
  message?: string;
  output?: any;
  payload?: any;
  error?: string;
  status?: string;
}

export interface NodeExecutionState {
  nodeId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  outputData?: any;
  error?: string;
  logs: string[];
}

export interface WorkflowExecutionState {
  executionId: string;
  workflowId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  nodeStates: Record<string, NodeExecutionState>;
  startTime: string;
  endTime?: string;
}
