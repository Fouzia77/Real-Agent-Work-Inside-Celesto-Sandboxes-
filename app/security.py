
"""Fail-closed command gate. Commands are logged before any guest execution."""
import re
from typing import Tuple

# This demo intentionally offers a narrow command surface rather than arbitrary shell access.
ALLOWED_PREFIXES = (
    "pwd", "ls", "cat ", "printf ", "echo ", "python --version",
    "python3 --version", "mkdir -p ", "python3 -c ", "test -f ",
    "sha256sum ", "find /workspace -maxdepth "
)
DENY_PATTERNS = [
    r"\brm\s+-rf\b", r"\bmkfs\b", r"\bdd\s+if=", r"\bshutdown\b",
    r"\breboot\b", r"\bcurl\b.*\b(API_KEY|TOKEN|SECRET)\b",
    r"\bwget\b.*\b(API_KEY|TOKEN|SECRET)\b", r"\bcat\s+\.env\b",
    r"\bprintenv\b", r"\benv\b\s*\|"
]

def check_command(command: str) -> Tuple[bool, str]:
    if not isinstance(command, str) or not command.strip():
        return False, "empty_command"
    cmd = command.strip()
    if any(re.search(pattern, cmd, flags=re.IGNORECASE) for pattern in DENY_PATTERNS):
        return False, "dangerous_command_pattern"
    if not any(cmd == prefix.strip() or cmd.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return False, "not_in_allowlist"
    return True, "allowlisted"
