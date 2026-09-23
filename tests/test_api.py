import importlib
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Reload saferoute.api with a fresh temp SQLite file so tests don't share state/DB."""
    import saferoute.api as api_module

    monkeypatch.setattr(api_module, "ROOT", api_module.ROOT)  # keep floor plan path
    api = importlib.reload(api_module)
    api.events.close()
    from saferoute.eventlog import EventLog

    api.events = EventLog(tmp_path / "events.db")
    api.state["node"], api.state["obs"] = "S", {}
    api.planner.reset()
    return TestClient(api.app)


def test_graph_endpoint(client):
    r = client.get("/api/graph")
    assert r.status_code == 200
    data = r.json()
    assert set(data["exits"]) == {"EXIT_A", "EXIT_B", "EXIT_C"}
    assert any(n["id"] == "S" for n in data["nodes"])


def test_state_endpoint_initial_recommendation(client):
    r = client.get("/api/state")
    body = r.json()
    assert body["event"] == "initial"
    assert body["path"][-1] == "EXIT_A"
    assert any(row["exit"] == "Exit A" and row["recommended"] for row in body["table"])


def test_post_observations_triggers_reroute(client):
    client.get("/api/state")  # establish the initial recommendation (Exit A) first
    r = client.post("/api/observations", json={"observations": {"S-JA": {"p_fire": 0.9}}})
    body = r.json()
    assert body["event"] == "reroute_blocked"
    assert body["path"][-1] == "EXIT_B"
    assert "fire" in body["headline"].lower()


def test_unknown_edge_id_returns_error(client):
    r = client.post("/api/observations", json={"observations": {"NOPE": {"p_fire": 0.9}}})
    assert "error" in r.json()


def test_unknown_node_returns_error(client):
    r = client.post("/api/position", json={"node": "NOPE"})
    assert "error" in r.json()


def test_events_are_logged_in_order(client):
    client.get("/api/state")
    client.post("/api/observations", json={"observations": {"S-JA": {"p_fire": 0.9}}})
    events = client.get("/api/events").json()
    assert len(events) >= 2
    assert events[0]["event"] == "reroute_blocked"  # most recent first
    assert any(e["event"] == "initial" for e in events)


def test_reset_clears_observations(client):
    client.post("/api/observations", json={"observations": {"S-JA": {"p_fire": 0.9}}})
    r = client.post("/api/reset")
    body = r.json()
    assert body["event"] == "initial"
    assert body["path"][-1] == "EXIT_A"


def test_websocket_receives_initial_state_and_broadcast():
    import saferoute.api as api
    from saferoute.eventlog import EventLog
    import tempfile, os

    tmp = tempfile.mktemp(suffix=".db")
    api.events.close()
    api.events = EventLog(tmp)
    api.state["node"], api.state["obs"] = "S", {}
    api.planner.reset()
    client = TestClient(api.app)

    with client.websocket_connect("/ws") as ws:
        first = ws.receive_json()
        assert first["event"] == "initial"
        client.post("/api/observations", json={"observations": {"S-JA": {"p_fire": 0.9}}})
        second = ws.receive_json()
        assert second["event"] == "reroute_blocked"
    api.events.close()
    os.remove(tmp)


def test_eventlog_persists_across_instances(tmp_path):
    from saferoute.eventlog import EventLog
    from saferoute.planner import RoutePlanner
    from saferoute.graph import BuildingGraph
    from saferoute.risk import RiskConfig
    from saferoute.explain import explain

    graph = BuildingGraph.from_json("data/floorplan_mall.json")
    cfg = RiskConfig()
    planner = RoutePlanner(graph, cfg)
    db = tmp_path / "ev.db"

    log1 = EventLog(db)
    d = planner.update({}, "S")
    log1.log(d, explain(d, graph, {}, cfg))
    log1.close()

    log2 = EventLog(db)
    rows = log2.recent()
    assert len(rows) == 1 and rows[0]["event"] == "initial"
    log2.close()