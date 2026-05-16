export interface NodeSchema {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    properties: Record<string, any>;
    credentials?: string; // ID of the credential to use
  };
}
