from collections import defaultdict
from typing import Any, Optional
from datetime import datetime
from core.events import bus, Event


class CXMetrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.events: list[dict[str, Any]] = []
        self.max_events = 5000

        # attach to event bus
        bus.subscribe(self._on_event)

    # -------------------------
    # EVENT HOOK
    # -------------------------

    def _on_event(self, event: Event):
        self.counters[f"event_{event.name}"] += 1
        self.counters[f"level_{event.level}"] += 1

        self.events.append({
            "name": event.name,
            "source": event.source,
            "level": event.level,
            "data": event.data,
            "timestamp": event.timestamp
        })

        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

    # -------------------------
    # MANUAL COUNTERS
    # -------------------------

    def inc(self, key: str, value: int = 1):
        self.counters[key] += value

    def event(self, name: str, data: Optional[dict] = None):
        bus.emit(Event(
            name=name,
            source="metrics",
            level="INFO",
            data=data or {}
        ))

    # -------------------------
    # SNAPSHOT (Prometheus / API)
    # -------------------------

    def snapshot(self) -> dict:
        return {
            "counters": dict(self.counters),
            "recent_events": self.events[-100:],
            "timestamp": datetime.utcnow().isoformat()
        }

    # -------------------------
    # SIMPLE EXPORT FORMAT (future Prometheus hook)
    # -------------------------

    def prometheus_format(self) -> str:
        lines = []
        for k, v in self.counters.items():
            lines.append(f"{k} {v}")
        return "\n".join(lines)


metrics = CXMetrics()