from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from core.config import (
    WORKSPACE_ROOT,
    API_HOST,
    API_PORT,
    SERVER_NAME,
    DEBUG,
)
from core.events import bus, Event
from core.metrics import metrics
from core.safety import safety
from core.executor import executor
from core.tools.registry import registry
from core.tools.base import ToolContext
from tools.discovery import load_all_tools


# =========================
# LOGGING SETUP
# =========================

log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

def bind_registry_tools() -> None:
    """Bind all registered tools to MCP server with proper error handling."""
    for tool in registry.all_tools():

        tool_name = tool.name
        tool_description = getattr(
            tool,
            "description",
            f"{tool_name} tool"
        )

        # Fix issue #2: Use default argument to avoid closure binding bug
        def make_handler(bound_tool: Any) -> Any:
            """Create handler with proper binding to prevent late-binding issues."""
            def handler(**kwargs: Any) -> Any:
                ctx = ToolContext(
                    dry_run=safety.dry_run
                )

                try:
                    return registry.run(
                        name=bound_tool.name,
                        payload=kwargs,
                        ctx=ctx
                    )
                except Exception as e:
                    # Fix issue #3: Add error handling in tool handler
                    logger.exception(f"Error executing tool {bound_tool.name}")
                    bus.emit(Event(
                        name="tool_handler_error",
                        source="CORE",
                        level="ERROR",
                        data={
                            "tool": bound_tool.name,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    ))
                    raise

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

def boot_system() -> None:
    """Initialize and boot the system."""
    load_all_tools()
    bind_registry_tools()

    tool_count = len(registry.all_tools())
    
    bus.emit(Event(
        name="system_boot",
        source="CORE",
        level="INFO",
        data={
            "workspace": str(WORKSPACE_ROOT),
            "server": SERVER_NAME,
            "tool_count": tool_count
        }
    ))

    logger.info(f"System boot complete. Loaded {tool_count} tools.")


# =========================
# METRICS
# =========================

def get_metrics_snapshot() -> dict[str, Any]:
    """Return current metrics snapshot."""
    return metrics.snapshot()


# =========================
# DEBUG EVENTS (OPTIONAL)
# =========================

def debug_event_printer(event: Event) -> None:
    """Print debug information for events."""
    print(
        f"[EVENT] "
        f"{event.source} - "
        f"{event.level} - "
        f"{event.name}"
    )


# bus.subscribe(debug_event_printer)


# =========================
# GRACEFUL SHUTDOWN
# =========================

def shutdown_gracefully() -> None:
    """Clean shutdown of executor and other resources."""
    logger.info("Initiating graceful shutdown...")
    try:
        executor.shutdown()
        logger.info("Executor shut down successfully.")
    except Exception as e:
        logger.error(f"Error during executor shutdown: {e}")


# =========================
# MCP RUNNER
# =========================

def run_mcp() -> None:
    """Run the MCP server."""
    boot_system()

    bus.emit(Event(
        name="mcp_start",
        source="CORE",
        level="INFO",
        data={
            "server": SERVER_NAME
        }
    ))

    logger.info(f"Starting MCP server: {SERVER_NAME}")
    mcp.run(transport="stdio")


# =========================
# FASTAPI HOOK (ISOLATED)
# =========================

async def run_api() -> None:
    """Run FastAPI metrics server (intended for separate process or async context)."""
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    @app.get("/metrics")
    def metrics_route() -> dict[str, Any]:
        return get_metrics_snapshot()

    @app.get("/health")
    def health() -> dict[str, str]:
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
        logger.info("KeyboardInterrupt received.")
        bus.emit(Event(
            name="system_shutdown",
            source="CORE",
            level="INFO"
        ))
        shutdown_gracefully()

    except Exception as e:
        logger.exception("Fatal error occurred.")
        bus.emit(Event(
            name="fatal_error",
            source="CORE",
            level="ERROR",
            data={
                "error": str(e),
                "error_type": type(e).__name__
            }
        ))
        shutdown_gracefully()
        raise
