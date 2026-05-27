from __future__ import annotations

from typing import Any

from core.tools.base import BaseTool, ToolContext
from core.events import bus


# =========================
# TOOL REGISTRY
# =========================

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    # -------------------------
    # REGISTER
    # -------------------------

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

        bus.log(
            "REGISTRY",
            "tool_registered",
            "INFO",
            {
                "tool": tool.name
            }
        )

    # -------------------------
    # RESOLVE
    # -------------------------

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)

        if tool is None:
            bus.log(
                "REGISTRY",
                "tool_not_found",
                "ERROR",
                {"tool": name}
            )

            raise ValueError(f"Tool not found: {name}")

        return tool

    # -------------------------
    # EXECUTE
    # -------------------------

    def run(
        self,
        name: str,
        payload: dict[str, Any],
        ctx: ToolContext
    ):
        tool = self.get(name)

        # registry metadata
        ctx.meta.setdefault("registry", True)
        ctx.meta.setdefault("tool_name", name)

        bus.log(
            "REGISTRY",
            "tool_dispatch",
            "INFO",
            {
                "tool": name,
                "dry_run": ctx.dry_run,
            }
        )

        try:
            result = tool.run(payload, ctx)

            bus.log(
                "REGISTRY",
                "tool_completed",
                "SUCCESS",
                {
                    "tool": name,
                    "result_type": type(result).__name__
                }
            )

            return result

        except Exception as e:
            bus.log(
                "REGISTRY",
                "tool_failed",
                "ERROR",
                {
                    "tool": name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    # -------------------------
    # DISCOVERY (NEW)
    # -------------------------

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def exists(self, name: str) -> bool:
        return name in self._tools


# =========================
# SINGLETON
# =========================

registry = ToolRegistry()