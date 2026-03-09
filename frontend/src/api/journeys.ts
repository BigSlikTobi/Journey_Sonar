import { apiFetch } from "./client";
import type { EdgeRead, NodeRead, NodeTree } from "../types";

export async function listRoots(): Promise<NodeRead[]> {
  return apiFetch<NodeRead[]>("/journey/roots");
}

export async function getTree(rootId: string): Promise<NodeTree> {
  return apiFetch<NodeTree>(`/journey/tree/${rootId}`);
}

export async function uploadJourney(file: File): Promise<NodeTree> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<NodeTree>("/journey/import", {
    method: "POST",
    body: form,
  });
}

export async function updateNode(
  nodeId: string,
  data: { name?: string; metadata?: Record<string, unknown>; position?: number },
): Promise<NodeRead> {
  return apiFetch<NodeRead>(`/journey/nodes/${nodeId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteNode(nodeId: string): Promise<void> {
  return apiFetch<void>(`/journey/nodes/${nodeId}`, { method: "DELETE" });
}

export async function createEdge(data: {
  source_node_id: string;
  target_node_id: string;
  metadata?: Record<string, unknown>;
}): Promise<EdgeRead> {
  return apiFetch<EdgeRead>("/journey/edges", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateEdge(
  edgeId: string,
  data: { metadata?: Record<string, unknown>; weight?: number },
): Promise<EdgeRead> {
  return apiFetch<EdgeRead>(`/journey/edges/${edgeId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteEdge(edgeId: string): Promise<void> {
  return apiFetch<void>(`/journey/edges/${edgeId}`, { method: "DELETE" });
}

export async function createNode(data: {
  name: string;
  type: "STAGE" | "TOUCHPOINT";
  parent_node_id: string;
  position: number;
  metadata?: Record<string, unknown>;
}): Promise<NodeRead> {
  return apiFetch<NodeRead>("/journey/nodes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
