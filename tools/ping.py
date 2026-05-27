from __future__ import annotations

from core.tools.base import BaseTool, ToolContext
from core.tools.registry import registry
from core.events import bus


class PingTool(BaseTool):
    name = "ping"

    # optional metadata (future MCP auto-binding)
    description = "Health check"

    # -------------------------
    # EXECUTE
    # -------------------------

    def execute(
        self,
        payload: dict[str, str],
        ctx: ToolContext
    ):
        message = payload.get("message", "pong")

        bus.log(
            "TOOLS",
            "ping_execute",
            "INFO",
            {
                "message": message
            }
        )

        return {
            "status": "ok",
            "echo": message,
            "tool": self.name
        }


# =========================
# SELF REGISTER
# =========================

registry.register(PingTool())