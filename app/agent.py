
"""Small deterministic agent task: create and verify a proof file inside the guest."""
import json
import time
from .celesto_executor import CelestoSession

TASK_COMMANDS = [
    "pwd",
    "mkdir -p /workspace",
    "printf 'celesto sandbox proof\\n' > /workspace/proof.txt",
    "cat /workspace/proof.txt",
    "sha256sum /workspace/proof.txt",
]

def run_proof_task(provider=None, inject_attack=False):
    started = time.monotonic()
    outputs = []
    with CelestoSession(provider=provider) as guest:
        boot_to_ready = time.monotonic() - guest.boot_started
        # The attack is intentionally denied before it reaches the guest.
        if inject_attack:
            attack = guest.run("cat .env")
            outputs.append({"step": "containment_attack", **attack})
        for i, command in enumerate(TASK_COMMANDS, start=1):
            result = guest.run(command)
            outputs.append({"step": i, "command": command, **result})
            if not result["ok"]:
                return {"success": False, "outputs": outputs, "wall_clock_s": time.monotonic()-started,
                        "boot_to_ready_s": boot_to_ready, "sandbox_name": guest.name}
        verified = any("celesto sandbox proof" in item.get("stdout", "") for item in outputs)
        return {"success": verified, "outputs": outputs, "wall_clock_s": time.monotonic()-started,
                "boot_to_ready_s": boot_to_ready, "sandbox_name": guest.name}
