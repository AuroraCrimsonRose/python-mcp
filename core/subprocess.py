from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.events import bus, Event
from core.metrics import metrics
from core.safety import safety


# =========================
# PROCESS RUNNER
# =========================

def run_command(
    cmd: list[str],
    cwd: str | None = None,
    timeout: int = 60
) -> dict[str, Any]:

    # -------------------------
    # VALIDATION
    # -------------------------

    if not cmd:
        raise ValueError(
            "Command list cannot be empty"
        )

    for item in cmd:
        if not isinstance(item, str):
            raise ValueError(
                "cmd must contain only strings"
            )

    executable = cmd[0].lower()

    # -------------------------
    # SAFETY CHECKS
    # -------------------------

    blocked_commands = {
        "rm",
        "rmdir",
        "del",
        "erase",
        "shutdown",
        "reboot",
        "mkfs",
        "format",
        "diskpart"
    }

    if executable in blocked_commands:
        bus.emit(Event(
            name="process_blocked",
            source="SUBPROCESS",
            level="ERROR",
            data={
                "cmd": cmd,
                "reason": "blocked_command"
            }
        ))

        metrics.inc(
            "subprocess_blocked"
        )

        return {
            "ok": False,
            "error": (
                f"Blocked command: "
                f"{executable}"
            ),
            "code": -1
        }

    resolved_cwd: Path | None = None

    if cwd is not None:
        resolved_cwd = (
            safety.validate_path(cwd)
        )

    # -------------------------
    # START EVENT
    # -------------------------

    bus.emit(Event(
        name="process_start",
        source="SUBPROCESS",
        level="INFO",
        data={
            "cmd": cmd,
            "cwd": str(resolved_cwd)
            if resolved_cwd else None,
            "timeout": timeout
        }
    ))

    metrics.inc(
        "subprocess_runs"
    )

    # -------------------------
    # EXECUTE
    # -------------------------

    try:
        result = subprocess.run(
            cmd,
            cwd=(
                str(resolved_cwd)
                if resolved_cwd
                else None
            ),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        stdout = (
            result.stdout or ""
        )

        stderr = (
            result.stderr or ""
        )

        ok = (
            result.returncode == 0
        )

        # -------------------------
        # COMPLETE EVENT
        # -------------------------

        bus.emit(Event(
            name="process_complete",
            source="SUBPROCESS",
            level=(
                "SUCCESS"
                if ok
                else "ERROR"
            ),
            data={
                "cmd": cmd,
                "code": result.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        ))

        return {
            "ok": ok,
            "stdout": stdout,
            "stderr": stderr,
            "code": result.returncode
        }

    # -------------------------
    # TIMEOUT
    # -------------------------

    except subprocess.TimeoutExpired:
        metrics.inc(
            "subprocess_timeouts"
        )

        bus.emit(Event(
            name="process_timeout",
            source="SUBPROCESS",
            level="ERROR",
            data={
                "cmd": cmd,
                "timeout": timeout
            }
        ))

        return {
            "ok": False,
            "error": "timeout",
            "code": -1
        }

    # -------------------------
    # UNEXPECTED ERROR
    # -------------------------

    except Exception as e:
        metrics.inc(
            "subprocess_errors"
        )

        bus.emit(Event(
            name="process_error",
            source="SUBPROCESS",
            level="ERROR",
            data={
                "cmd": cmd,
                "error": str(e)
            }
        ))

        return {
            "ok": False,
            "error": str(e),
            "code": -1
        }