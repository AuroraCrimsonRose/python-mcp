from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from collections.abc import Awaitable
from datetime import datetime
import asyncio
import uuid


# =========================
# EVENT MODEL (GRAPH-AWARE)
# =========================

@dataclass
class Event:
    name: str
    source: str
    level: str = "INFO"
    data: dict[str, Any] | None = None

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_event_id: str | None = None

    meta: dict[str, Any] = field(default_factory=dict)

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# =========================
# EVENT BUS
# =========================

class EventBus:
    def __init__(self):
        self._subscribers: list[Callable[[Event], Any]] = []
        self._async_subscribers: list[Callable[[Event], Awaitable[Any]]] = []

        self._current_trace: str | None = None
        self._current_parent: str | None = None

    # -------------------------
    # SUBSCRIBE
    # -------------------------

    def subscribe(self, fn: Callable[[Event], Any]):
        self._subscribers.append(fn)

    def subscribe_async(self, fn: Callable[[Event], Awaitable[Any]]):
        self._async_subscribers.append(fn)

    # -------------------------
    # TRACE CONTROL
    # -------------------------

    def start_trace(self) -> str:
        trace_id = str(uuid.uuid4())
        self._current_trace = trace_id
        self._current_parent = None
        return trace_id

    def set_parent(self, event_id: str | None):
        self._current_parent = event_id

    # -------------------------
    # EMIT (CORE SAFE PATH)
    # -------------------------

    def emit(self, event: Event):
        # inject trace
        if not event.trace_id:
            event.trace_id = self._current_trace or event.trace_id

        event.parent_event_id = event.parent_event_id or self._current_parent

        # advance causal chain
        self._current_parent = event.event_id

        # sync subscribers
        for fn in self._subscribers:
            try:
                fn(event)
            except Exception:
                pass

        # async subscribers (SAFE FIX)
        if self._async_subscribers:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return  # no loop available

            for fn in self._async_subscribers:
                try:
                    coro = fn(event)

                    # IMPORTANT FIX:
                    # ensure it's actually awaitable before scheduling
                    if asyncio.iscoroutine(coro):
                        loop.create_task(coro)

                except Exception:
                    pass

    # -------------------------
    # STRICT ASYNC EMIT
    # -------------------------

    async def emit_async(self, event: Event):
        for fn in self._subscribers:
            try:
                fn(event)
            except Exception:
                pass

        await asyncio.gather(
            *(fn(event) for fn in self._async_subscribers),
            return_exceptions=True
        )

    # -------------------------
    # LOG CONVENIENCE
    # -------------------------

    def log(
        self,
        source: str,
        name: str,
        level: str = "INFO",
        data: dict[str, Any] | None = None
    ):
        self.emit(
            Event(
                name=name,
                source=source,
                level=level,
                data=data or {}
            )
        )


# =========================
# SINGLETON
# =========================

bus = EventBus()