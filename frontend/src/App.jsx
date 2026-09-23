import React, { useEffect, useRef, useState } from "react";
import FloorPlanMap from "./components/FloorPlanMap.jsx";
import ExitTable from "./components/ExitTable.jsx";
import DecisionPanel from "./components/DecisionPanel.jsx";
import EventLogPanel from "./components/EventLogPanel.jsx";
import Controls from "./components/Controls.jsx";
import { getGraph, getEvents, setPosition, postObservations, reset, connectWebSocket } from "./api.js";

export default function App() {
  const [graph, setGraph] = useState(null);
  const [state, setState] = useState(null);
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("connecting");
  const [voiceOn, setVoiceOn] = useState(false);
  const lastSpoken = useRef("");

  useEffect(() => {
    getGraph().then(setGraph).catch(() => {});
    getEvents().then(setEvents).catch(() => {});
    const close = connectWebSocket(
      (payload) => {
        setState(payload);
        getEvents().then(setEvents).catch(() => {}); // cheap refresh; fine at this scale (Step 4's SQLite log)
      },
      setStatus
    );
    return close;
  }, []);

  useEffect(() => {
    if (!voiceOn || !state?.voice || state.voice === lastSpoken.current) return;
    lastSpoken.current = state.voice;
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(state.voice));
    }
  }, [state, voiceOn]);

  const move = (node) => setPosition(node).then(setState);
  const inject = (edge, obs) => postObservations({ [edge]: obs }).then(setState);
  const doReset = () => reset(graph?.nodes.find((n) => n.kind !== "exit")?.id || "S").then(setState);

  return (
    <div className="app">
      <header>
        <h1>SafeRoute Emergency AI</h1>
        <span className="subtitle">Academic prototype — not a certified emergency system</span>
      </header>

      <div className="layout">
        <div className="col-main">
          <FloorPlanMap graph={graph} edgeStatus={state?.edges} path={state?.path || []} currentNode={state?.current_node} onSelectNode={move} />
          <DecisionPanel state={state} voiceOn={voiceOn} onToggleVoice={setVoiceOn} />
          <ExitTable rows={state?.table} />
        </div>
        <div className="col-side">
          <Controls graph={graph} currentNode={state?.current_node || "S"} onMove={move} onInject={inject} onReset={doReset} status={status} />
          <EventLogPanel events={events} />
        </div>
      </div>
    </div>
  );
}
