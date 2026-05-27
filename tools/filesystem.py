from __future__ import annotations

from pathlib import Path
from typing import Any

from core.events import bus
from core.safety import safety
from core.tools.base import BaseTool, ToolContext
from core.tools.registry import registry


class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Safe filesystem operations"

    # =========================
    # EXECUTE
    # =========================

    def execute(
        self,
        payload: dict[str, Any],
        ctx: ToolContext
    ):
        action = str(payload.get("action", "")).strip()

        bus.log(
            "FILESYSTEM",
            "filesystem_execute",
            "INFO",
            {
                "action": action
            }
        )

        match action:
            case "read_file":
                return self.read_file(payload)

            case "write_file":
                return self.write_file(payload)

            case "list_dir":
                return self.list_dir(payload)

            case "exists":
                return self.exists(payload)

            case "mkdir":
                return self.mkdir(payload)

            case _:
                raise ValueError(
                    f"Unknown filesystem action: {action}"
                )

    # =========================
    # READ FILE
    # =========================

    def read_file(
        self,
        payload: dict[str, Any]
    ):
        path_value = payload.get("path")

        if not isinstance(path_value, str):
            raise ValueError("path must be string")

        path = safety.validate_path(path_value)

        return {
            "path": str(path),
            "content": path.read_text(
                encoding="utf-8"
            )
        }

    # =========================
    # WRITE FILE
    # =========================

    def write_file(
        self,
        payload: dict[str, Any]
    ):
        path_value = payload.get("path")
        content_value = payload.get("content")

        if not isinstance(path_value, str):
            raise ValueError("path must be string")

        if not isinstance(content_value, str):
            raise ValueError(
                "content must be string"
            )

        path = safety.validate_path(path_value)

        safety.check_file_write(
            path,
            content_value
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        path.write_text(
            content_value,
            encoding="utf-8"
        )

        return {
            "ok": True,
            "path": str(path),
            "bytes_written": len(
                content_value.encode("utf-8")
            )
        }

    # =========================
    # LIST DIRECTORY
    # =========================

    def list_dir(
        self,
        payload: dict[str, Any]
    ):
        path_value = payload.get(
            "path",
            "."
        )

        if not isinstance(path_value, str):
            raise ValueError(
                "path must be string"
            )

        path = safety.validate_path(
            path_value
        )

        entries: list[dict[str, Any]] = []

        for item in path.iterdir():
            entries.append(
                {
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "is_file": item.is_file()
                }
            )

        return {
            "path": str(path),
            "count": len(entries),
            "entries": entries
        }

    # =========================
    # EXISTS
    # =========================

    def exists(
        self,
        payload: dict[str, Any]
    ):
        path_value = payload.get("path")

        if not isinstance(path_value, str):
            raise ValueError(
                "path must be string"
            )

        path = safety.validate_path(
            path_value
        )

        return {
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir(),
            "is_file": path.is_file()
        }

    # =========================
    # MKDIR
    # =========================

    def mkdir(
        self,
        payload: dict[str, Any]
    ):
        path_value = payload.get("path")

        if not isinstance(path_value, str):
            raise ValueError(
                "path must be string"
            )

        path = safety.validate_path(
            path_value
        )

        path.mkdir(
            parents=True,
            exist_ok=True
        )

        return {
            "ok": True,
            "path": str(path)
        }


# =========================
# SELF REGISTER
# =========================

registry.register(
    FilesystemTool()
)