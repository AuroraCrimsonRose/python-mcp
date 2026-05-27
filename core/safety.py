from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable

import asyncio

from core.config import (
    WORKSPACE_ROOT,
    MAX_FILE_SIZE,
    IGNORE_DIRS,
    DRY_RUN_DEFAULT,
)

from core.events import bus, Event
from core.metrics import metrics


# =========================
# SAFETY ERROR
# =========================

class SafetyError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# =========================
# SAFETY ENGINE
# =========================

class SafetyEngine:
    def __init__(self):
        self.dry_run = DRY_RUN_DEFAULT
        self.block_destructive = True

    # -------------------------
    # MODE CONTROL
    # -------------------------

    def set_dry_run(self, value: bool):
        self.dry_run = value
        bus.emit(Event(
            name="safety_dry_run",
            source="SAFETY",
            level="INFO",
            data={"enabled": value}
        ))

    # -------------------------
    # PATH SANDBOXING
    # -------------------------

    def validate_path(self, path: str) -> Path:
        target = (WORKSPACE_ROOT / path).resolve()

        if not str(target).startswith(str(WORKSPACE_ROOT)):
            self._violation("PATH_ESCAPE", path)
            raise SafetyError("PATH_ESCAPE", "Outside workspace")

        for part in target.parts:
            if part in IGNORE_DIRS:
                self._violation("IGNORED_PATH", path)
                raise SafetyError("IGNORED_PATH", f"Blocked directory: {part}")

        return target

    # -------------------------
    # FILE SIZE GUARD
    # -------------------------

    def check_file_write(self, path: Path, content: str):
        if len(content.encode("utf-8")) > MAX_FILE_SIZE:
            self._violation("FILE_TOO_LARGE", str(path))
            raise SafetyError("FILE_TOO_LARGE", "Exceeded limit")

    # -------------------------
    # DESTRUCTIVE OPS
    # -------------------------

    def allow_action(self, action: str):
        blocked = {
            "delete_file",
            "rm_rf",
            "format",
            "wipe",
            "drop_db",
        }

        if self.block_destructive and action in blocked:
            self._violation("DESTRUCTIVE_BLOCK", action)
            raise SafetyError("DESTRUCTIVE_BLOCK", f"Blocked: {action}")

    # =========================================================
    # ASYNC SAFE WRAPPER (NEW CORE ENTRYPOINT)
    # =========================================================

    async def wrap_async(
        self,
        tool_name: str,
        fn: Callable[..., Any | Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        bus.emit(Event(
            name="tool_start",
            source="SAFETY",
            level="INFO",
            data={"tool": tool_name}
        ))

        if self.dry_run:
            return {
                "dry_run": True,
                "tool": tool_name,
                "args": args,
                "kwargs": kwargs,
            }

        try:
            result = fn(*args, **kwargs)

            if asyncio.iscoroutine(result):
                result = await result

            metrics.inc(f"tool_{tool_name}")
            metrics.inc("tools_executed")

            bus.emit(Event(
                name="tool_success",
                source="SAFETY",
                level="SUCCESS",
                data={"tool": tool_name}
            ))

            return result

        except SafetyError as e:
            bus.emit(Event(
                name="tool_blocked",
                source="SAFETY",
                level="ERROR",
                data={"code": e.code, "message": e.message}
            ))

            metrics.inc("safety_blocks")

            return {"error": True, "code": e.code, "message": e.message}

        except Exception as e:
            bus.emit(Event(
                name="tool_crash",
                source="SAFETY",
                level="ERROR",
                data={"tool": tool_name, "error": str(e)}
            ))

            metrics.inc("tool_errors")

            return {"error": True, "code": "UNEXPECTED", "message": str(e)}

    # -------------------------
    # INTERNAL VIOLATION LOGGER
    # -------------------------

    def _violation(self, code: str, context: str):
        bus.emit(Event(
            name="safety_violation",
            source="SAFETY",
            level="ERROR",
            data={"code": code, "context": context}
        ))

        metrics.inc(f"safety_{code}")


# singleton
safety = SafetyEngine()