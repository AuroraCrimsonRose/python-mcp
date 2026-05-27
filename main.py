from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from core.config import (
    WORKSPACE_ROOT,
    API_HOST,
    API_PORT,
    SERVER_NAME,
)
from core.events import bus, Event
from core.metrics import metrics
from core.safety import safety
from core.executor import executor
from core.tools.registry import registry
from core.tools.base import ToolContext
from tools.discovery import load_all_tools


# =========================
# RUNTIME BOOTSTRAP
# =========================

executor.start()


# =========================
# MCP SERVER
# =========================

mcp = FastMCP(SERVER_NAME)


# =========================
# REGISTRY → MCP AUTO BIND
# =========================

def bind_registry_tools():
    for tool in registry.all_tools():

        tool_name = tool.name
        tool_description = getattr(
            tool,
            "description",
            f"{tool_name} tool"
        )

        def make_handler(bound_tool):
            def handler(**kwargs):
                ctx = ToolContext(
                    dry_run=safety.dry_run
                )

                return registry.run(
                    name=bound_tool.name,
                    payload=kwargs,
                    ctx=ctx
                )

            return handler

        mcp.tool(
            name=tool_name,
            description=tool_description
        )(make_handler(tool))

        bus.log(
            "CORE",
            "mcp_tool_bound",
            "INFO",
            {
                "tool": tool_name
            }
        )


# =========================
# SYSTEM BOOT
# =========================

def boot_system():
    load_all_tools()
    bind_registry_tools()

    bus.emit(Event(
        name="system_boot",
        source="CORE",
        level="INFO",
        data={
            "workspace": str(WORKSPACE_ROOT),
            "server": SERVER_NAME,
            "tool_count": len(registry._tools)
        }
    ))


# =========================
# METRICS
# =========================

def get_metrics_snapshot():
    return metrics.snapshot()


# =========================
# DEBUG EVENTS (OPTIONAL)
# =========================

def debug_event_printer(event: Event):
    print(
        f"[EVENT] "
        f"{event.source} - "
        f"{event.level} - "
        f"{event.name}"
    )


# bus.subscribe(debug_event_printer)


# =========================
# MCP RUNNER
# =========================

def run_mcp():
    boot_system()

    bus.emit(Event(
        name="mcp_start",
        source="CORE",
        level="INFO",
        data={
            "server": SERVER_NAME
        }
    ))

    mcp.run(transport="stdio")


# =========================
# FASTAPI HOOK (ISOLATED)
# =========================

async def run_api():
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    @app.get("/metrics")
    def metrics_route():
        return get_metrics_snapshot()

    @app.get("/health")
    def health():
        return {
            "status": "ok"
        }

    config = uvicorn.Config(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )

    server = uvicorn.Server(config)

    await server.serve()


# =========================
# ENTRYPOINT
# =========================

if __name__ == "__main__":
    try:
        run_mcp()

    except KeyboardInterrupt:
        bus.emit(Event(
            name="system_shutdown",
            source="CORE",
            level="INFO"
        ))

    except Exception as e:
        bus.emit(Event(
            name="fatal_error",
            source="CORE",
            level="ERROR",
            data={
                "error": str(e)
            }
        ))
        raise