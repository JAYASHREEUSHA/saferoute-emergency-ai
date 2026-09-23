import React from "react";

export default function EventLogPanel({ events }) {
  return (
    <div className="panel">
      <h2>Event log</h2>
      <div className="event-log">
        {events.length === 0 && <div className="muted">No events yet.</div>}
        {events.map((e) => (
          <div key={e.id} className="event-row">
            <span className="event-time">{new Date(e.ts * 1000).toLocaleTimeString()}</span>
            <span className="event-text">{e.headline}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
