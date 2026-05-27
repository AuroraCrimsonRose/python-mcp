from __future__ import annotations

from typing import Any

from core.subprocess import run_command
from core.tools.base import BaseTool, ToolContext
from core.tools.registry import registry


class SubprocessTool(BaseTool):
    name = "subprocess"
    description = "Run a subprocess command safely"

    # =========================
    # EXECUTE
    # =========================

    def execute(
        self,
        payload: dict[str, Any],
        ctx: ToolContext
    ):
        cmd = payload.get("cmd")

        if not isinstance(cmd, list):
            raise ValueError(
                "cmd must be list[str]"
            )

        cwd = payload.get("cwd")

        if cwd is not None and not isinstance(
            cwd,
            str
        ):
            raise ValueError(
                "cwd must be string"
            )

        timeout = payload.get(
            "timeout",
            60
        )

        if not isinstance(
            timeout,
            int
        ):
            raise ValueError(
                "timeout must be int"
            )

        return run_command(
            cmd=cmd,
            cwd=cwd,
            timeout=timeout
        )


# =========================
# SELF REGISTER
# =========================

registry.register(
    SubprocessTool()
)