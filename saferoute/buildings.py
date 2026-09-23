"""Building generators. The 8-node demo mall is too small to show route diversity,
so experiments also run on a grid of corridors with several exits."""
from __future__ import annotations

import random

from .graph import BuildingGraph, Edge, Node


def grid_building(
    rows: int = 4,
    cols: int = 6,
    spacing: float = 10.0,
    width: float = 3.0,
    exits: set[tuple[int, int]] | None = None,
    camera_coverage: float = 1.0,
    rng: random.Random | None = None,
) -> BuildingGraph:
    """rows x cols lattice of junctions joined by corridors. Exits default to the four corners.

    camera_coverage < 1 leaves a random fraction of corridors without a camera
    (those use the unknown-coverage prior in the risk model)."""
    rng = rng or random.Random(0)
    exits = exits if exits is not None else {(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)}
    exit_names = {rc: f"Exit {i + 1}" for i, rc in enumerate(sorted(exits))}

    nodes = []
    for i in range(rows):
        for j in range(cols):
            is_exit = (i, j) in exits
            nodes.append(
                Node(
                    id=f"N{i}_{j}",
                    x=j * spacing,
                    y=(rows - 1 - i) * spacing,
                    kind="exit" if is_exit else "junction",
                    label=exit_names[(i, j)] if is_exit else f"J{i}_{j}",
                )
            )

    edges = []

    def add(a: tuple[int, int], b: tuple[int, int]) -> None:
        eid = f"N{a[0]}_{a[1]}-N{b[0]}_{b[1]}"
        cam = f"cam_{len(edges)}" if rng.random() < camera_coverage else None
        edges.append(
            Edge(id=eid, u=f"N{a[0]}_{a[1]}", v=f"N{b[0]}_{b[1]}", length=spacing, width=width,
                 camera=cam, label=f"Corridor {a[0]}{a[1]}-{b[0]}{b[1]}")
        )

    for i in range(rows):
        for j in range(cols):
            if j + 1 < cols:
                add((i, j), (i, j + 1))
            if i + 1 < rows:
                add((i, j), (i + 1, j))
    return BuildingGraph(f"grid {rows}x{cols}", nodes, edges)
