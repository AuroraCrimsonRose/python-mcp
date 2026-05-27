from __future__ import annotations

import sys
from datetime import datetime

from loguru import logger

from core.config import LOG_DIR
from core.events import Event, bus


class CXLoggerSink:
    def __init__(self):
        logger.remove()

        # =========================
        # SESSION LOG FILE
        # =========================

        timestamp = datetime.utcnow().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        self.log_path = LOG_DIR / (
            f"MCP-{timestamp}.log"
        )

        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # =========================
        # CONSOLE LOGGER
        # =========================

        logger.add(
            sys.stderr,
            level="DEBUG",
            colorize=True,
            backtrace=False,
            diagnose=False,
            format=(
                "<level>{level:<8}</level> | "
                "<cyan>{extra[module]:<12}</cyan> | "
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{message}"
            )
        )

        # =========================
        # FILE LOGGER
        # =========================

        logger.add(
            str(self.log_path),
            level="DEBUG",
            enqueue=True,
            retention="30 days",
            compression="zip",
            backtrace=False,
            diagnose=False,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level:<8} | "
                "{extra[module]:<12} | "
                "{message}"
            )
        )

        logger.bind(module="LOGGER").info(
            f"Session log created: {self.log_path.name}"
        )

    # =========================
    # EVENT HANDLER
    # =========================

    def handle(
        self,
        event: Event
    ):
        module = event.source.upper()
        level = event.level.lower()

        message = event.name

        if event.data:
            message += (
                f" | {event.data}"
            )

        with logger.contextualize(
            module=module
        ):
            log_method = getattr(
                logger,
                level,
                logger.info
            )

            log_method(message)

    # =========================
    # OPTIONAL DIRECT ACCESS
    # =========================

    def get_log_path(self) -> str:
        return str(self.log_path)


# =========================
# SINGLETON
# =========================

cxlog_sink = CXLoggerSink()


# =========================
# REGISTER TO EVENT BUS
# =========================

bus.subscribe(
    cxlog_sink.handle
)