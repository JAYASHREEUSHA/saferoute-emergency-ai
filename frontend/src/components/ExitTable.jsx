import React from "react";

const STATUS_CLASS = { Low: "ok", Medium: "warn", High: "danger", Blocked: "danger", Unreachable: "danger" };

export default function ExitTable({ rows }) {
  if (!rows?.length) return null;
  return (
    <div className="panel">
      <h2>Exits</h2>
      <table className="exit-table">
        <thead>
          <tr>
            <th>Exit</th><th>Status</th><th>Dist (m)</th><th>Time (s)</th><th>Risk</th><th>Cost</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.exit} className={r.recommended ? "recommended" : ""}>
              <td>{r.recommended ? "★ " : ""}{r.exit}</td>
              <td><span className={`badge ${STATUS_CLASS[r.status] || ""}`}>{r.status}</span></td>
              <td>{r.distance_m ?? "–"}</td>
              <td>{r.travel_time_s ?? "–"}</td>
              <td>{r.route_risk != null ? `${Math.round(r.route_risk * 100)}%` : "–"}</td>
              <td>{r.cost ?? "–"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
