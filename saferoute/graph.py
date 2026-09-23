"""Building graph: nodes (junctions/exits), edges (corridors) and JSON loading."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Node:
    id: str
    x: float
    y: float
    kind: str = "junction"  # "start" | "junction" | "exit"
    label: str = ""


@dataclass(frozen=True)
class Edge:
    id: str
    u: str
    v: str
    length: float  # metres
    width: float = 3.0  # metres, used for crowd density (people / m^2)
    camera: str | None = None  # camera covering this corridor, if any
    label: str = ""

    @property
    def area(self) -> float:
        return self.length * self.width

    def other(self, node_id: str) -> str:
        return self.v if node_id == self.u else self.u


class BuildingGraph:
    def __init__(self, name: str, nodes: list[Node], edges: list[Edge]):
        self.name = name
        self.nodes: dict[str, Node] = {}
        for n in nodes:
            if n.id in self.nodes:
                raise ValueError(f"duplicate node id: {n.id}")
            self.nodes[n.id] = n

        self.edges: dict[str, Edge] = {}
        self.adj: dict[str, list[tuple[str, str]]] = {nid: [] for nid in self.nodes}
        for e in edges:
            if e.id in self.edges:
                raise ValueError(f"duplicate edge id: {e.id}")
            for end in (e.u, e.v):
                if end not in self.nodes:
                    raise ValueError(f"edge {e.id} references unknown node {end}")
            if e.length + 1e-9 < self.euclid(e.u, e.v):
                # A* heuristic (straight line / free-flow speed) stays admissible only if
                # no corridor is shorter than the straight-line distance.
                raise ValueError(f"edge {e.id}: length {e.length} < straight-line distance")
            self.edges[e.id] = e
            self.adj[e.u].append((e.v, e.id))
            self.adj[e.v].append((e.u, e.id))

        self.exits: list[str] = [n.id for n in nodes if n.kind == "exit"]
        if not self.exits:
            raise ValueError("floor plan needs at least one exit node")

    # ---- geometry helpers -------------------------------------------------
    def euclid(self, a: str, b: str) -> float:
        na, nb = self.nodes[a], self.nodes[b]
        return math.hypot(na.x - nb.x, na.y - nb.y)

    def label(self, node_id: str) -> str:
        return self.nodes[node_id].label or node_id

    def edge_between(self, u: str, v: str) -> Edge | None:
        for nb, eid in self.adj[u]:
            if nb == v:
                return self.edges[eid]
        return None

    # ---- loading ----------------------------------------------------------
    @classmethod
    def from_dict(cls, d: dict) -> "BuildingGraph":
        nodes = [
            Node(n["id"], float(n["x"]), float(n["y"]), n.get("kind", "junction"), n.get("label", ""))
            for n in d["nodes"]
        ]
        pos = {n.id: n for n in nodes}
        edges = []
        for e in d["edges"]:
            length = e.get("length")
            if length is None:
                a, b = pos[e["u"]], pos[e["v"]]
                length = math.hypot(a.x - b.x, a.y - b.y)
            edges.append(
                Edge(
                    id=e["id"], u=e["u"], v=e["v"], length=float(length),
                    width=float(e.get("width", 3.0)), camera=e.get("camera"),
                    label=e.get("label", ""),
                )
            )
        return cls(d.get("name", "unnamed"), nodes, edges)

    @classmethod
    def from_json(cls, path: str | Path) -> "BuildingGraph":
        return cls.from_dict(json.loads(Path(path).read_text()))
