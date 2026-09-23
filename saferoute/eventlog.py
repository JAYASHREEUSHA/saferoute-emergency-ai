"""SQLite event log: every decision the planner makes, for the dashboard's history panel
and for post-hoc analysis. One row per planner update (not per frame)."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .explain import Explanation
from .planner import Decision

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    event TEXT NOT NULL,
    current_node TEXT NOT NULL,
    recommended_exit TEXT,
    route_risk REAL,
    headline TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    table_json TEXT NOT NULL
);
"""


class EventLog:
    def __init__(self, path: str | Path = "saferoute_events.db"):
        self.path = str(path)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def log(self, decision: Decision, ex: Explanation, ts: float | None = None) -> int:
        rec = decision.recommended
        cur = self._conn.execute(
            "INSERT INTO events (ts, event, current_node, recommended_exit, route_risk, headline, "
            "reasons_json, table_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ts if ts is not None else time.time(),
                decision.event,
                decision.current_node,
                rec.exit_id if rec else None,
                rec.route_risk if rec else None,
                ex.headline,
                json.dumps(ex.reasons),
                json.dumps(ex.table),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def recent(self, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, ts, event, current_node, recommended_exit, route_risk, headline, reasons_json, table_json "
            "FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        out = []
        for r in rows:
            out.append(
                dict(
                    id=r[0], ts=r[1], event=r[2], current_node=r[3], recommended_exit=r[4],
                    route_risk=r[5], headline=r[6], reasons=json.loads(r[7]), table=json.loads(r[8]),
                )
            )
        return out

    def close(self) -> None:
        self._conn.close()