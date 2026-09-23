import React from "react";

const PAD = 40;

function riskColor(edge) {
  if (!edge) return "#4b5563"; // no data yet: neutral grey
  if (edge.blocked) return "#dc2626"; // red: impassable
  const r = Math.max(edge.p_fire, edge.p_smoke, edge.p_block);
  if (r > 0.5) return "#f59e0b"; // amber: high
  if (r > 0.15) return "#eab308"; // yellow: medium
  return edge.monitored ? "#16a34a" : "#6b7280"; // green: clear (monitored) / grey: unmonitored
}

export default function FloorPlanMap({ graph, edgeStatus, path, currentNode, onSelectNode }) {
  if (!graph) return <div className="panel map-panel">Loading floor plan…</div>;

  const xs = graph.nodes.map((n) => n.x);
  const ys = graph.nodes.map((n) => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const w = maxX - minX || 1, h = maxY - minY || 1;
  const scale = Math.min(560 / w, 360 / h);
  const vbW = w * scale + PAD * 2, vbH = h * scale + PAD * 2;

  const pos = (id) => {
    const n = graph.nodes.find((n) => n.id === id);
    return { x: (n.x - minX) * scale + PAD, y: (maxY - n.y) * scale + PAD }; // flip y: north is up
  };

  const pathEdges = new Set();
  for (let i = 0; i + 1 < path.length; i++) {
    const e = graph.edges.find((e) => (e.u === path[i] && e.v === path[i + 1]) || (e.v === path[i] && e.u === path[i + 1]));
    if (e) pathEdges.add(e.id);
  }

  return (
    <div className="panel map-panel">
      <svg viewBox={`0 0 ${vbW} ${vbH}`} width="100%" height="100%" role="img" aria-label={graph.name}>
        {graph.edges.map((e) => {
          const a = pos(e.u), b = pos(e.v);
          const status = edgeStatus?.[e.id];
          const onPath = pathEdges.has(e.id);
          return (
            <g key={e.id}>
              <line
                x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke={riskColor(status)}
                strokeWidth={onPath ? 7 : 4}
                strokeLinecap="round"
                opacity={onPath ? 1 : 0.85}
              />
              {onPath && (
                <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#fff" strokeWidth={1.5} strokeDasharray="2 6" opacity={0.8} />
              )}
            </g>
          );
        })}

        {graph.nodes.map((n) => {
          const p = pos(n.id);
          const isExit = n.kind === "exit";
          const isCurrent = n.id === currentNode;
          return (
            <g key={n.id} onClick={() => onSelectNode?.(n.id)} style={{ cursor: onSelectNode ? "pointer" : "default" }}>
              <circle cx={p.x} cy={p.y} r={isExit ? 10 : 5} fill={isExit ? "#0ea5e9" : "#1f2937"} stroke="#fff" strokeWidth={isCurrent ? 3 : 1} />
              {isCurrent && <circle cx={p.x} cy={p.y} r={16} fill="none" stroke="#fbbf24" strokeWidth={2} />}
              <text x={p.x} y={p.y - (isExit ? 16 : 10)} textAnchor="middle" fontSize="11" fill="#e5e7eb">
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="legend">
        <span><i className="dot" style={{ background: "#16a34a" }} /> clear</span>
        <span><i className="dot" style={{ background: "#eab308" }} /> medium</span>
        <span><i className="dot" style={{ background: "#f59e0b" }} /> high</span>
        <span><i className="dot" style={{ background: "#dc2626" }} /> blocked</span>
        <span><i className="dot" style={{ background: "#6b7280" }} /> unmonitored</span>
      </div>
    </div>
  );
}
