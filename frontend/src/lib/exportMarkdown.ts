import type { EdgeRead, NodeRead, NodeTree, TouchpointMetadata } from "../types";

function flattenTree(tree: NodeTree): { nodes: NodeRead[]; edges: EdgeRead[] } {
  const nodes: NodeRead[] = [tree.node];
  const edges: EdgeRead[] = [...tree.edges];
  for (const child of tree.children) {
    const r = flattenTree(child);
    nodes.push(...r.nodes);
    edges.push(...r.edges);
  }
  return { nodes, edges };
}

export function generateMarkdown(tree: NodeTree): string {
  const version = (tree.node.metadata as Record<string, string>)?.version;
  const date = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  const { nodes, edges } = flattenTree(tree);
  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));

  let md = `# ${tree.node.name}\n\n`;
  if (version) md += `**Version:** ${version}  \n`;
  md += `**Exported:** ${date}\n\n`;
  md += `---\n\n`;

  tree.children.forEach((stage, si) => {
    md += `## Stage ${si + 1}: ${stage.node.name}\n\n`;

    if (stage.children.length === 0) {
      md += `*No touchpoints.*\n\n`;
    }

    stage.children.forEach((tp) => {
      const meta = tp.node.metadata as unknown as TouchpointMetadata;
      md += `### ${tp.node.name}\n\n`;

      if (meta?.businessRule) {
        md += `**Business Rule**\n\n${meta.businessRule}\n\n`;
      }
      if (meta?.feature) {
        md += `**Feature**\n\n${meta.feature}\n\n`;
      }
      if (meta?.dataPoints?.length) {
        md += `**Data Points**\n\n${meta.dataPoints.map((d) => `- ${d}`).join("\n")}\n\n`;
      }
      if (meta?.edgeCases?.length) {
        md += `**Edge Cases**\n\n${meta.edgeCases.map((e) => `- ${e}`).join("\n")}\n\n`;
      }
      if (meta?.emails?.length) {
        md += `**Emails**\n\n| Name | Subject |\n|---|---|\n`;
        md += meta.emails.map((e) => `| ${e.name} | ${e.subject} |`).join("\n");
        md += "\n\n";
      }
    });

    md += "---\n\n";
  });

  if (edges.length > 0) {
    md += `## Connections\n\n`;
    edges.forEach((edge) => {
      const src = nodeMap[edge.source_node_id]?.name ?? edge.source_node_id;
      const tgt = nodeMap[edge.target_node_id]?.name ?? edge.target_node_id;
      const label = (edge.metadata?.label as string | undefined) ?? "";
      md += `- **${src}** → **${tgt}**`;
      if (label) md += ` *(${label})*`;
      md += "\n";
    });
    md += "\n";
  }

  return md;
}
