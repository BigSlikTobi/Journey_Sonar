import type { EdgeRead, NodeRead, NodeTree, TouchpointMetadata } from "../types";

const STAGE_W = 240;
const STAGE_H = 60;
const TP_W = 220;
const TP_H_BASE = 80;
const TP_Y_GAP = 12;
const STAGE_X_GAP = 320;
const CANVAS_X = 40;
const CANVAS_Y = 40;
const TP_Y_OFFSET = 90;

function esc(s: string) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function collectNodes(tree: NodeTree, map: Record<string, NodeRead>) {
  map[tree.node.id] = tree.node;
  tree.children.forEach((c) => collectNodes(c, map));
}

function collectEdges(tree: NodeTree, out: EdgeRead[]) {
  out.push(...tree.edges);
  tree.children.forEach((c) => collectEdges(c, out));
}

export function generateDrawioXml(tree: NodeTree): string {
  const nodeMap: Record<string, NodeRead> = {};
  collectNodes(tree, nodeMap);
  const allEdges: EdgeRead[] = [];
  collectEdges(tree, allEdges);

  const cells: string[] = [];

  tree.children.forEach((stage, stageIndex) => {
    const sx = CANVAS_X + stageIndex * STAGE_X_GAP;
    const sy = CANVAS_Y;

    cells.push(
      `<mxCell id="stage-${stage.node.id}" value="${esc(stage.node.name)}" ` +
        `style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF2FF;strokeColor=#A5B4FC;fontStyle=1;fontSize=11;fontColor=#1f2937;" ` +
        `vertex="1" parent="1">` +
        `<mxGeometry x="${sx}" y="${sy}" width="${STAGE_W}" height="${STAGE_H}" as="geometry"/>` +
        `</mxCell>`
    );

    stage.children.forEach((tp, tpIndex) => {
      const meta = tp.node.metadata as unknown as TouchpointMetadata;
      const dpCount = meta?.dataPoints?.length ?? 0;
      const ecCount = meta?.edgeCases?.length ?? 0;
      const emailCount = meta?.emails?.length ?? 0;

      const feature = meta?.feature ? esc(meta.feature.slice(0, 80)) + (meta.feature.length > 80 ? "…" : "") : "";
      const summary = [
        dpCount > 0 ? `${dpCount} data pts` : "",
        ecCount > 0 ? `${ecCount} edge cases` : "",
        emailCount > 0 ? `${emailCount} emails` : "",
      ]
        .filter(Boolean)
        .join(" · ");

      // HTML tags must be XML-encoded when placed inside an attribute value.
      // draw.io with html=1 decodes &lt;b&gt; back to <b> for rendering.
      const lines: string[] = [`&lt;b&gt;${esc(tp.node.name)}&lt;/b&gt;`];
      if (feature) lines.push(feature);
      if (summary) lines.push(`&lt;i&gt;${summary}&lt;/i&gt;`);
      const value = lines.join("&lt;br&gt;");

      // Estimate height based on content lines
      const extraLines = lines.length - 1;
      const height = TP_H_BASE + extraLines * 14;

      const tx = sx + (STAGE_W - TP_W) / 2;
      const ty = CANVAS_Y + TP_Y_OFFSET + tpIndex * (TP_H_BASE + TP_Y_GAP);

      cells.push(
        `<mxCell id="tp-${tp.node.id}" value="${value}" ` +
          `style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#E5E7EB;fontSize=10;align=left;verticalAlign=top;spacingLeft=6;spacingTop=4;" ` +
          `vertex="1" parent="1">` +
          `<mxGeometry x="${tx}" y="${ty}" width="${TP_W}" height="${height}" as="geometry"/>` +
          `</mxCell>`
      );
    });
  });

  allEdges.forEach((edge) => {
    const label = esc((edge.metadata?.label as string) ?? "");
    cells.push(
      `<mxCell id="edge-${edge.id}" value="${label}" ` +
        `style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" ` +
        `edge="1" source="tp-${edge.source_node_id}" target="tp-${edge.target_node_id}" parent="1">` +
        `<mxGeometry relative="1" as="geometry"/>` +
        `</mxCell>`
    );
  });

  return `<?xml version="1.0" encoding="UTF-8"?>\n<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>${cells.join("")}</root></mxGraphModel>`;
}

export function downloadDrawio(tree: NodeTree): void {
  const xml = generateDrawioXml(tree);
  const blob = new Blob([xml], { type: "application/xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${tree.node.name.replace(/[^a-z0-9_-]/gi, "_")}-journey.drawio`;
  a.click();
  URL.revokeObjectURL(url);
}
