
"""Commands run inside an existing Celesto computer."""
import re
import uuid
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .security import check_command

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "logs" / "commands.jsonl"


def _utc():
    return datetime.now(timezone.utc).isoformat()

def new_sandbox_name():
    return "sbx-" + uuid.uuid4().hex[:12]


def append_audit(name: str, command: str, decision: str):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": _utc(),
        "sandbox_name": name,
        "command": command,
        "decision": decision,
        "execution_target": "celesto_sandbox",
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


class CelestoSession:
    """Attach to an existing Celesto computer without owning its lifecycle."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("CELESTO_PROVIDER", "cloud")).lower()
        self.computer = None
        self.computer_id = os.getenv("CELESTO_COMPUTER_ID", "").strip()
        self.name = new_sandbox_name()
        self.boot_started = time.monotonic()

    def __enter__(self):
        if self.provider not in {"cloud", "local"}:
            raise ValueError("CELESTO_PROVIDER must be 'cloud' or 'local'")
        if not self.computer_id:
            raise RuntimeError("Set CELESTO_COMPUTER_ID to an existing computer ID")
        if self.provider == "cloud" and not os.getenv("CELESTO_API_KEY"):
            raise RuntimeError("Set CELESTO_API_KEY before attaching to a cloud computer")

        from celesto import Computer
        self.computer = Computer.get(self.computer_id, provider=self.provider)
        return self

    def run(self, command: str):
        if self.computer is None:
            raise RuntimeError("Celesto session is not open")

        allowed, reason = check_command(command)
        append_audit(self.name, command, "allow" if allowed else "block")
        if not allowed:
            return {
                "ok": False,
                "exit_code": 126,
                "stdout": "",
                "stderr": f"blocked by safety gate: {reason}",
            }

        result = self.computer.run(command)
        return {
            "ok": getattr(result, "exit_code", 1) == 0,
            "exit_code": getattr(result, "exit_code", 1),
            "stdout": getattr(result, "stdout", "") or "",
            "stderr": getattr(result, "stderr", "") or "",
        }

    def __exit__(self, exc_type, exc, tb):
        # Close only this attached handle; do not delete the existing computer.
        if self.computer is not None:
            self.computer.close()
        return False
