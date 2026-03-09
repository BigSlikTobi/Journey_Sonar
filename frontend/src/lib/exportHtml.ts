import type { EdgeRead, NodeRead, NodeTree, TouchpointMetadata } from "../types";

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

export function generateJourneyHtml(tree: NodeTree): string {
  const nodeMap: Record<string, NodeRead> = {};
  collectNodes(tree, nodeMap);
  const allEdges: EdgeRead[] = [];
  collectEdges(tree, allEdges);

  const version = (tree.node.metadata as Record<string, string>)?.version ?? "";
  const date = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });

  const stagesHtml = tree.children
    .map((stage) => {
      const tpsHtml = stage.children
        .map((tp) => {
          const meta = tp.node.metadata as unknown as TouchpointMetadata;
          const dpCount = meta?.dataPoints?.length ?? 0;
          const ecCount = meta?.edgeCases?.length ?? 0;
          const emailCount = meta?.emails?.length ?? 0;

          const featureHtml = meta?.feature
            ? `<p class="tp-text">${esc(meta.feature)}</p>`
            : `<p class="tp-empty">—</p>`;

          const brHtml =
            [
              meta?.businessRule ? `<p class="tp-text">${esc(meta.businessRule)}</p>` : "",
              ecCount > 0
                ? `<ul class="tp-list amber">${meta.edgeCases.map((e) => `<li>${esc(e)}</li>`).join("")}</ul>`
                : "",
            ].join("") || `<p class="tp-empty">—</p>`;

          const dpHtml =
            dpCount > 0
              ? `<ul class="tp-list">${meta.dataPoints.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>`
              : `<p class="tp-empty">—</p>`;

          const emailsHtml =
            emailCount > 0
              ? `<ul class="tp-list">${meta.emails
                  .map(
                    (e) =>
                      `<li><strong>${esc(e.name)}</strong>${e.subject ? `<span class="email-sub"> — ${esc(e.subject)}</span>` : ""}</li>`
                  )
                  .join("")}</ul>`
              : `<p class="tp-empty">—</p>`;

          const chips = [
            dpCount > 0 ? `<span class="chip blue" data-hide-hl="dataPoints">${dpCount} data pts</span>` : "",
            ecCount > 0 ? `<span class="chip amber" data-hide-hl="businessRule">${ecCount} edge cases</span>` : "",
            emailCount > 0 ? `<span class="chip purple" data-hide-hl="emails">${emailCount} emails</span>` : "",
          ]
            .filter(Boolean)
            .join("");

          return `<div class="tp-card">
  <div class="tp-name">${esc(tp.node.name)}</div>
  <div class="tp-content" data-hl="feature">${featureHtml}</div>
  <div class="tp-content" data-hl="businessRule" style="display:none">${brHtml}</div>
  <div class="tp-content" data-hl="dataPoints" style="display:none">${dpHtml}</div>
  <div class="tp-content" data-hl="emails" style="display:none">${emailsHtml}</div>
  ${chips ? `<div class="chips">${chips}</div>` : ""}
</div>`;
        })
        .join("\n");

      return `<div class="stage-col">
  <div class="stage-node">
    <p class="stage-label">Stage</p>
    <p class="stage-name">${esc(stage.node.name)}</p>
  </div>
  <div class="stage-tps">${tpsHtml || '<p class="no-tp">No touchpoints</p>'}</div>
</div>`;
    })
    .join("\n");

  const connectionsHtml =
    allEdges.length > 0
      ? `<div class="connections-section">
  <p class="connections-title">Connections</p>
  <div class="connections-list">
    ${allEdges
      .map((e) => {
        const from = esc(nodeMap[e.source_node_id]?.name ?? e.source_node_id);
        const to = esc(nodeMap[e.target_node_id]?.name ?? e.target_node_id);
        const label = esc((e.metadata?.label as string) ?? "");
        return `<div class="conn-row"><span class="conn-from">${from}</span><span class="conn-arrow">→</span><span class="conn-to">${to}</span>${label ? `<span class="conn-label">${label}</span>` : ""}</div>`;
      })
      .join("\n")}
  </div>
</div>`
      : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(tree.node.name)} — Journey Sonar</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f3f4f6;color:#111827}

/* ── top bar ── matches app's dark nav */
.topbar{background:#111827;padding:.75rem 1rem;display:flex;align-items:center;justify-content:space-between}
.brand{font-size:.875rem;font-weight:600;color:#fff}
.filter-wrap{display:flex;align-items:center;gap:.375rem}
.filter-label{font-size:.75rem;color:#9ca3af}
.hl-select{border-radius:.375rem;border:1px solid #4b5563;background:#1f2937;padding:.25rem .5rem;font-size:.75rem;color:#d1d5db;cursor:pointer}
.hl-select option{background:#1f2937;color:#fff}

/* ── journey sub-header ── matches the graph header bar */
.journey-header{padding:.625rem 1rem;display:flex;align-items:baseline;gap:.75rem;flex-wrap:wrap;background:#fff;border-bottom:1px solid #e5e7eb}
.journey-title{font-size:1.125rem;font-weight:700;color:#111827}
.journey-version{font-size:.75rem;color:#9ca3af}
.journey-hint{font-size:.75rem;color:#9ca3af}

/* ── canvas ── matches React Flow bg */
.canvas{padding:1.5rem;overflow-x:auto;min-height:calc(100vh - 100px);background-color:#f9fafb;background-image:radial-gradient(circle,#e5e7eb 1px,transparent 1px);background-size:20px 20px}

/* ── stages row ── horizontal like the graph */
.stages-row{display:flex;gap:80px;align-items:flex-start;width:max-content;padding:.5rem}

/* ── stage column ── */
.stage-col{display:flex;flex-direction:column;align-items:center;gap:12px;width:240px}

/* ── stage node ── matches StageNode */
.stage-node{width:240px;border-radius:.5rem;border:2px solid #a5b4fc;background:#eef2ff;box-shadow:0 1px 2px rgba(0,0,0,.05);padding:.5rem .75rem;user-select:none}
.stage-label{font-size:.625rem;font-weight:700;color:#4338ca;text-transform:uppercase;letter-spacing:.05em}
.stage-name{font-size:.875rem;font-weight:600;color:#1f2937;line-height:1.3;margin-top:.1rem}

/* ── stage touchpoints column ── */
.stage-tps{display:flex;flex-direction:column;gap:12px;width:220px}
.no-tp{font-size:.75rem;color:#d1d5db;text-align:center}

/* ── touchpoint card ── matches TouchpointNode */
.tp-card{width:220px;border-radius:.5rem;border:1px solid #e5e7eb;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.05);padding:.5rem .75rem}
.tp-name{font-size:.875rem;font-weight:600;color:#111827;line-height:1.3;padding-bottom:.375rem;margin-bottom:.375rem;border-bottom:1px solid #f9fafb}
.tp-content{margin-bottom:.25rem}
.tp-text{font-size:.6875rem;color:#9ca3af;white-space:pre-wrap;line-height:1.45}
.tp-empty{font-size:.6875rem;color:#d1d5db;font-style:italic}
.tp-list{font-size:.6875rem;color:#9ca3af;padding-left:.875rem;line-height:1.5}
.tp-list li{margin-bottom:.1rem}
.tp-list.amber li{color:#d97706}
.email-sub{color:#d1d5db;font-weight:400}

/* ── chips ── match the Chip component */
.chips{display:flex;flex-wrap:wrap;gap:.25rem;margin-top:.375rem}
.chip{border-radius:9999px;padding:.125rem .375rem;font-size:.625rem;font-weight:500}
.chip.blue{background:#eff6ff;color:#2563eb}
.chip.amber{background:#fffbeb;color:#d97706}
.chip.purple{background:#faf5ff;color:#7c3aed}

/* ── connections ── */
.connections-section{margin-top:1.5rem;padding:1rem 1.25rem;background:#fff;border-radius:.75rem;border:1px solid #e5e7eb;box-shadow:0 1px 2px rgba(0,0,0,.05);width:max-content;max-width:calc(100vw - 3rem)}
.connections-title{font-size:.75rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.625rem}
.connections-list{display:flex;flex-direction:column;gap:.375rem}
.conn-row{display:flex;align-items:center;gap:.5rem;font-size:.8125rem;color:#374151}
.conn-arrow{color:#9ca3af;font-size:.875rem}
.conn-label{font-size:.6875rem;color:#6366f1;background:#eef2ff;border-radius:9999px;padding:.125rem .5rem;font-style:italic}
</style>
</head>
<body>

<div class="topbar">
  <span class="brand">Journey Sonar</span>
  <div class="filter-wrap">
    <span class="filter-label">Show:</span>
    <select id="hlSelect" class="hl-select" onchange="setHL(this.value)">
      <option value="feature">Feature</option>
      <option value="businessRule">Business Rule</option>
      <option value="dataPoints">Data Points</option>
      <option value="emails">Emails</option>
    </select>
  </div>
</div>

<div class="journey-header">
  <span class="journey-title">${esc(tree.node.name)}</span>
  ${version ? `<span class="journey-version">v${esc(version)}</span>` : ""}
  <span class="journey-hint">— ${esc(date)} · read-only export</span>
</div>

<div class="canvas">
  <div class="stages-row">
    ${stagesHtml}
  </div>
  ${connectionsHtml}
</div>

<script>
function setHL(v){
  document.querySelectorAll('.tp-content').forEach(function(el){
    el.style.display=el.getAttribute('data-hl')===v?'':'none';
  });
  document.querySelectorAll('[data-hide-hl]').forEach(function(el){
    el.style.display=el.getAttribute('data-hide-hl')===v?'none':'';
  });
  document.getElementById('hlSelect').value=v;
}
setHL('feature');
</script>
</body>
</html>`;
}
