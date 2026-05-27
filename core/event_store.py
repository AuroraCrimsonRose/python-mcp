from collections import deque
from typing import Optional, Any, Callable, Iterator

from core.events import Event, bus


class EventStore:
    def __init__(self, max_size: int = 10_000):
        self.buffer: deque[Event] = deque(maxlen=max_size)
        self._cursor: int = 0

        bus.subscribe(self._capture)

    # =========================
    # CAPTURE
    # =========================

    def _capture(self, event: Event):
        event.meta["cursor"] = self._cursor

        self.buffer.append(event)
        self._cursor += 1

    # =========================
    # QUERY
    # =========================

    def query(
        self,
        source: Optional[str] = None,
        level: Optional[str] = None,
        name: Optional[str] = None,
        start_cursor: Optional[int] = None,
        end_cursor: Optional[int] = None,
    ) -> list[Event]:

        events = list(self.buffer)

        if source is not None:
            events = [e for e in events if e.source == source]

        if level is not None:
            events = [e for e in events if e.level == level]

        if name is not None:
            events = [e for e in events if e.name == name]

        def cursor_of(e: Event) -> int:
            return e.meta.get("cursor", -1)

        if start_cursor is not None:
            events = [e for e in events if cursor_of(e) >= start_cursor]

        if end_cursor is not None:
            events = [e for e in events if cursor_of(e) <= end_cursor]

        return events

    # =========================
    # PAGINATION
    # =========================

    def page(self, cursor: int = 0, limit: int = 100) -> dict[str, Any]:
        events = list(self.buffer)
        sliced = events[cursor:cursor + limit]

        return {
            "cursor": cursor,
            "next_cursor": cursor + len(sliced),
            "count": len(sliced),
            "events": sliced
        }

    # =========================
    # REPLAY
    # =========================

    def replay(
        self,
        source: Optional[str] = None,
        level: Optional[str] = None,
        name: Optional[str] = None,
        handler: Optional[Callable[[Event], Any]] = None,
    ):
        for event in self.query(source, level, name):
            if handler:
                handler(event)
            else:
                bus.emit(event)

    # =========================
    # REVERSE DEBUG
    # =========================

    def replay_reverse(self, handler: Callable[[Event], Any]):
        for event in reversed(self.buffer):
            handler(event)

    # =========================
    # STREAM TAIL
    # =========================

    def tail(self, last_n: int = 50) -> Iterator[Event]:
        yield from list(self.buffer)[-last_n:]


# singleton
event_store = EventStore()