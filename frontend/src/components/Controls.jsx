import React from "react";

// A few illustrative hazard buttons matching the mall's 3-exit scripted scenario from Step 1.
const DEMO_HAZARDS = [
  { label: "Fire on Corridor A", edge: "S-JA", obs: { p_fire: 0.9 } },
  { label: "Crowd on Corridor B", edge: "JB-EXIT_B", obs: { people: 150 } },
  { label: "Smoke on Corridor C", edge: "C1-C2", obs: { p_smoke: 0.85 } },
];

export default function Controls({ graph, currentNode, onMove, onInject, onReset, status }) {
  if (!graph) return null;
  const junctions = graph.nodes.filter((n) => n.kind !== "exit");

  return (
    <div className="panel">
      <h2>
        Controls
        <span className={`conn-dot ${status}`} title={`WebSocket: ${status}`} />
      </h2>

      <div className="control-row">
        <label>User position</label>
        <select value={currentNode} onChange={(e) => onMove(e.target.value)}>
          {junctions.map((n) => (
            <option key={n.id} value={n.id}>{n.label}</option>
          ))}
        </select>
      </div>

      <div className="control-row">
        <label>Simulate a hazard</label>
        <div className="button-row">
          {DEMO_HAZARDS.map((h) => (
            <button key={h.label} onClick={() => onInject(h.edge, h.obs)}>{h.label}</button>
          ))}
        </div>
      </div>

      <button className="reset-btn" onClick={onReset}>Reset scenario</button>
    </div>
  );
}
