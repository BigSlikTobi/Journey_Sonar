import type { EdgeRead, NodeRead, NodeTree, TouchpointMetadata } from "../types";

function collectNodes(tree: NodeTree, map: Record<string, NodeRead>) {
  map[tree.node.id] = tree.node;
  tree.children.forEach((c) => collectNodes(c, map));
}

function collectEdges(tree: NodeTree, out: EdgeRead[]) {
  out.push(...tree.edges);
  tree.children.forEach((c) => collectEdges(c, out));
}

export function generateJourneyJson(tree: NodeTree): string {
  const nodeMap: Record<string, NodeRead> = {};
  collectNodes(tree, nodeMap);

  const allEdges: EdgeRead[] = [];
  collectEdges(tree, allEdges);

  const version = (tree.node.metadata as Record<string, string>)?.version;

  const stages = tree.children.map((stage) => ({
    title: stage.node.name,
    items: stage.children.map((tp) => {
      const meta = tp.node.metadata as unknown as TouchpointMetadata;
      return {
        touchpoint: tp.node.name,
        businessRule: meta?.businessRule ?? "",
        feature: meta?.feature ?? "",
        dataPoints: meta?.dataPoints ?? [],
        edgeCases: meta?.edgeCases ?? [],
        emails: meta?.emails ?? [],
      };
    }),
  }));

  const connections = allEdges.map((edge) => {
    const from = nodeMap[edge.source_node_id]?.name ?? edge.source_node_id;
    const to = nodeMap[edge.target_node_id]?.name ?? edge.target_node_id;
    const label = (edge.metadata?.label as string | undefined) ?? "";
    return label ? { from, to, label } : { from, to };
  });

  const payload: Record<string, unknown> = { journeyName: tree.node.name };
  if (version) payload.version = version;
  payload.stages = stages;
  if (connections.length > 0) payload.connections = connections;

  return JSON.stringify(payload, null, 2);
}

export function downloadJourneyJson(tree: NodeTree): void {
  const json = generateJourneyJson(tree);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${tree.node.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-journey.json`;
  a.click();
  URL.revokeObjectURL(url);
}
