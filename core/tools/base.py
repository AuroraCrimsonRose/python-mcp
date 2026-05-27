from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from core.events import bus


# =========================
# TOOL CONTEXT
# =========================

@dataclass
class ToolContext:
    user: str | None = None
    dry_run: bool = False

    # safe mutable metadata container
    meta: dict[str, Any] = field(default_factory=dict)


# =========================
# TOOL CONTRACT
# =========================

class Tool(Protocol):
    name: str

    def execute(self, payload: dict[str, Any], ctx: ToolContext) -> Any:
        ...


# =========================
# BASE TOOL
# =========================

class BaseTool:
    name: str = "base"

    # -------------------------
    # LIFECYCLE WRAPPER
    # -------------------------

    def run(self, payload: dict[str, Any], ctx: ToolContext):
        bus.log(self.name, "tool_start", "INFO", {"payload": payload})

        try:
            # attach execution metadata (useful for event graph later)
            ctx.meta.setdefault("tool", self.name)
            ctx.meta.setdefault("dry_run", ctx.dry_run)

            if ctx.dry_run:
                result = self.preview(payload, ctx)
            else:
                result = self.execute(payload, ctx)

            bus.log(
                self.name,
                "tool_success",
                "SUCCESS",
                {
                    "result_type": type(result).__name__,
                    "result": repr(result)[:500]  # prevent log explosion
                }
            )

            return result

        except Exception as e:
            bus.log(
                self.name,
                "tool_error",
                "ERROR",
                {
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            )
            raise

    # -------------------------
    # OVERRIDABLE
    # -------------------------

    def execute(self, payload: dict[str, Any], ctx: ToolContext):
        raise NotImplementedError("Tool must implement execute()")

    def preview(self, payload: dict[str, Any], ctx: ToolContext):
        return {
            "dry_run": True,
            "tool": self.name,
            "payload": payload
        }