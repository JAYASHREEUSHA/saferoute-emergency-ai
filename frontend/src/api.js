const BASE = ""; // same-origin; Vite dev server proxies /api and /ws to FastAPI (see vite.config.js)

export async function getGraph() {
  const r = await fetch(`${BASE}/api/graph`);
  return r.json();
}

export async function getState() {
  const r = await fetch(`${BASE}/api/state`);
  return r.json();
}

export async function setPosition(node) {
  const r = await fetch(`${BASE}/api/position`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node }),
  });
  return r.json();
}

export async function postObservations(observations) {
  const r = await fetch(`${BASE}/api/observations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ observations }),
  });
  return r.json();
}

export async function reset(node = "S") {
  const r = await fetch(`${BASE}/api/reset?node=${encodeURIComponent(node)}`, { method: "POST" });
  return r.json();
}

export async function getEvents(limit = 50) {
  const r = await fetch(`${BASE}/api/events?limit=${limit}`);
  return r.json();
}

/** Opens the live WebSocket. onMessage receives every decision payload (same shape as getState()).
 * Auto-reconnects with backoff if the backend restarts (e.g. --reload picked up a code change). */
export function connectWebSocket(onMessage, onStatusChange) {
  let ws;
  let closedByUser = false;
  let retryDelay = 1000;

  function open() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen = () => {
      retryDelay = 1000;
      onStatusChange?.("connected");
    };
    ws.onmessage = (ev) => {
      try {
        onMessage(JSON.parse(ev.data));
      } catch {
        // ignore malformed frames
      }
    };
    ws.onclose = () => {
      onStatusChange?.("disconnected");
      if (!closedByUser) {
        setTimeout(open, retryDelay);
        retryDelay = Math.min(retryDelay * 1.5, 10000);
      }
    };
    ws.onerror = () => ws.close();
  }
  open();

  return () => {
    closedByUser = true;
    ws?.close();
  };
}
