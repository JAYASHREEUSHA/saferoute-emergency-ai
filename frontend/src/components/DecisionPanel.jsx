import React from "react";

const EVENT_TONE = {
  initial: "info",
  keep: "info",
  reroute_blocked: "warn",
  reroute_better: "warn",
  no_safe_route: "danger",
  arrived: "ok",
};

export default function DecisionPanel({ state, voiceOn, onToggleVoice }) {
  if (!state) return <div className="panel">Waiting for the first decision…</div>;
  const tone = EVENT_TONE[state.event] || "info";
  return (
    <div className="panel">
      <div className={`headline ${tone}`}>{state.headline}</div>
      <label className="voice-toggle">
        <input type="checkbox" checked={voiceOn} onChange={(e) => onToggleVoice(e.target.checked)} />
        Speak instructions aloud
      </label>
      <ul className="reasons">
        {state.reasons?.map((r, i) => <li key={i}>{r}</li>)}
      </ul>
    </div>
  );
}
