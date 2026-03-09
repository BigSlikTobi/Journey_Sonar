export type NodeType = "JOURNEY_ROOT" | "STAGE" | "TOUCHPOINT" | "MICRO_ACTION";

export interface NodeRead {
  id: string;
  workspace_id: string;
  name: string;
  type: NodeType;
  parent_node_id: string | null;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  metadata: Record<string, unknown>;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface EdgeRead {
  id: string;
  workspace_id: string;
  source_node_id: string;
  target_node_id: string;
  condition: Record<string, unknown> | null;
  is_fallback: boolean;
  weight: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface NodeTree {
  node: NodeRead;
  children: NodeTree[];
  edges: EdgeRead[];
}

export interface TouchpointMetadata {
  businessRule: string;
  feature: string;
  dataPoints: string[];
  edgeCases: string[];
  emails: { name: string; subject: string }[];
}
