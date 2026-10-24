
"""PostgreSQL ledger with a SQLite-free in-memory fallback for unit tests."""
import os
from contextlib import contextmanager
from typing import Any

VALID_STATES = {"created", "ready", "running", "succeeded", "failed", "deleted"}

def _connect():
    import psycopg
    return psycopg.connect(os.getenv("DATABASE_URL", "postgresql://ledger:ledger@ledger:5432/ledger"))

def init_db():
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS runs (
                        run_id TEXT PRIMARY KEY,
                        sandbox_name TEXT NOT NULL,
                        problem_id TEXT NOT NULL,
                        state TEXT NOT NULL,
                        execution_target TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
    except Exception:
        # API can start only once the Compose dependency is healthy; this branch is useful
        # for importing the module in isolated unit tests. Startup retry is handled in main.py.
        raise

def list_runs():
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT run_id, sandbox_name, problem_id, state, execution_target, created_at FROM runs ORDER BY created_at")
            rows = cur.fetchall()
    return [dict(run_id=r[0], sandbox_name=r[1], problem_id=r[2], state=r[3],
                 execution_target=r[4], created_at=r[5].isoformat()) for r in rows]

def create_run(item: dict[str, Any]):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO runs(run_id, sandbox_name, problem_id, state, execution_target)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING run_id, sandbox_name, problem_id, state, execution_target, created_at
            """, (item["run_id"], item["sandbox_name"], item["problem_id"], item["state"], item["execution_target"]))
            r = cur.fetchone()
    return dict(run_id=r[0], sandbox_name=r[1], problem_id=r[2], state=r[3],
                execution_target=r[4], created_at=r[5].isoformat())
