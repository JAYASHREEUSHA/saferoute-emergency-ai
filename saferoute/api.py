"""FastAPI backend for the SafeRoute dashboard (Step 5 frontend talks to this).

Single-session MVP: one simulated user, one shared building. Observations are posted in
(from the mocked scenario, the vision layer, or a manual test) and every update is logged
and broadcast to connected WebSocket clients.

Run:  uvicorn saferoute.api:app --reload
Docs: http://127.0.0.1:8000/docs (FastAPI's automatic Swagger UI)
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .eventlog import EventLog
from .explain import explain
from .graph import BuildingGraph
from .planner import RoutePlanner
from .risk import EdgeObservation, RiskConfig

ROOT = Path(__file__).resolve().parents[1]

app = FastAPI(title="SafeRoute Emergency AI", version="0.4.0")

graph = BuildingGraph.from_json(ROOT / "data" / "floorplan_mall.json")
risk_cfg = RiskConfig()
planner = RoutePlanner(graph, risk_cfg)
events = EventLog(ROOT / "saferoute_events.db")

state = {"node": "S", "obs": {}}  # obs: edge_id -> EdgeObservation
sockets: set[WebSocket] = set()


class ObservationIn(BaseModel):
    p_fire: float = 0.0
    p_smoke: float = 0.0
    p_block: float = 0.0
    people: float = 0.0


class ObservationsIn(BaseModel):
    observations: dict[str, ObservationIn]


class PositionIn(BaseModel):
    node: str


def _decide_and_log() -> dict:
    decision = planner.update(state["obs"], state["node"])
    ex = explain(decision, graph, state["obs"], risk_cfg)
    events.log(decision, ex)
    return {
        "event": decision.event,
        "current_node": decision.current_node,
        "headline": ex.headline,
        "voice": ex.voice,
        "reasons": ex.reasons,
        "table": ex.table,
        "path": decision.recommended.path if decision.recommended else [],
    }


async def _broadcast(payload: dict) -> None:
    dead = []
    for ws in sockets:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        sockets.discard(ws)


@app.get("/api/graph")
def get_graph() -> dict:
    return {
        "name": graph.name,
        "nodes": [{"id": n.id, "x": n.x, "y": n.y, "kind": n.kind, "label": n.label} for n in graph.nodes.values()],
        "edges": [{"id": e.id, "u": e.u, "v": e.v, "length": e.length, "camera": e.camera, "label": e.label} for e in graph.edges.values()],
        "exits": graph.exits,
    }


@app.get("/api/state")
def get_state() -> dict:
    return _decide_and_log()


@app.post("/api/position")
async def set_position(p: PositionIn) -> dict:
    if p.node not in graph.nodes:
        return {"error": f"unknown node id: {p.node}"}
    state["node"] = p.node
    payload = _decide_and_log()
    await _broadcast(payload)
    return payload


@app.post("/api/observations")
async def post_observations(body: ObservationsIn) -> dict:
    for eid, o in body.observations.items():
        if eid not in graph.edges:
            return {"error": f"unknown edge id: {eid}"}
        state["obs"][eid] = EdgeObservation(p_fire=o.p_fire, p_smoke=o.p_smoke, p_block=o.p_block, people=o.people)
    payload = _decide_and_log()
    await _broadcast(payload)
    return payload


@app.post("/api/reset")
async def reset(node: str = "S") -> dict:
    state["obs"] = {}
    state["node"] = node
    planner.reset()
    payload = _decide_and_log()
    await _broadcast(payload)
    return payload


@app.get("/api/events")
def get_events(limit: int = 50) -> list[dict]:
    return events.recent(limit)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    sockets.add(ws)
    await ws.send_json(_decide_and_log())  # initial state on connect
    try:
        while True:
            await ws.receive_text()  # client doesn't need to send anything; keeps the connection open
    except WebSocketDisconnect:
        sockets.discard(ws)