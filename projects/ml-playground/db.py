"""SQLite storage for ML Playground experiments."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "experiments.db"


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                model_name TEXT NOT NULL,
                params_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                artifacts_json TEXT NOT NULL,
                note TEXT
            );
            """
        )
        conn.commit()


def add_experiment(
    *,
    model_name: str,
    params: Dict[str, Any],
    metrics: Dict[str, Any],
    artifacts: Dict[str, Any],
    note: str,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO experiments (created_at, model_name, params_json, metrics_json, artifacts_json, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                model_name,
                json.dumps(params),
                json.dumps(metrics),
                json.dumps(artifacts),
                note or None,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "model_name": row["model_name"],
        "params": json.loads(row["params_json"]),
        "metrics": json.loads(row["metrics_json"]),
        "artifacts": json.loads(row["artifacts_json"]),
        "note": row["note"] or "",
    }


def list_experiments(limit: int = 20) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM experiments
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_row_to_dict(row) for row in rows]


def get_experiment(experiment_id: int) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM experiments WHERE id = ?",
            (experiment_id,),
        ).fetchone()
        if not row:
            return None
        return _row_to_dict(row)
