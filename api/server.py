from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from pydantic import BaseModel

from core.metrics import metrics
from core.events import bus, Event
from core.config import API_HOST, API_PORT
from core.event_store import event_store

app = FastAPI(title="CXOS MCP API", version="1.0")

# =========================
# MODELS
# =========================

class ReplayRequest(BaseModel):
    source: str | None = None
    level: str | None = None
    name: str | None = None


# =========================
# WEBSOCKET STATE
# =========================

connected_clients: List[WebSocket] = []


# =========================
# EVENT BROADCAST
# =========================

async def broadcast(event: Event):
    dead_clients = []

    payload = {
        "name": event.name,
        "source": event.source,
        "level": event.level,
        "data": event.data,
        "timestamp": event.timestamp,
    }

    for ws in connected_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead_clients.append(ws)

    for ws in dead_clients:
        if ws in connected_clients:
            connected_clients.remove(ws)


# subscribe once
bus.subscribe_async(broadcast)


# =========================
# HEALTH / METRICS
# =========================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "cxos-mcp"
    }


@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()


@app.get("/metrics/prometheus")
def prometheus_metrics():
    return metrics.prometheus_format()


# =========================
# LIVE EVENT STREAM
# =========================

@app.websocket("/ws/events")
async def event_stream(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)

    bus.emit(Event(
        name="client_connected",
        source="API",
        level="INFO",
        data={"clients": len(connected_clients)}
    ))

    try:
        while True:
            # lightweight keep-alive loop
            await ws.receive_text()

    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)

        bus.emit(Event(
            name="client_disconnected",
            source="API",
            level="INFO",
            data={"clients": len(connected_clients)}
        ))


# =========================
# EVENT REPLAY (READ ONLY)
# =========================

@app.get("/events/replay")
def replay_events(
    source: str | None = None,
    level: str | None = None,
    name: str | None = None
):
    events = event_store.query(source, level, name)

    return {
        "count": len(events),
        "events": [
            {
                "name": e.name,
                "source": e.source,
                "level": e.level,
                "data": e.data,
                "timestamp": e.timestamp,
            }
            for e in events
        ]
    }


# =========================
# EVENT REPLAY (EXECUTION)
# =========================

@app.post("/events/replay/run")
def replay_run(req: ReplayRequest):

    def printer(event):
        print(f"[REPLAY] {event.source} | {event.name}")

    event_store.replay(
        source=req.source,
        level=req.level,
        name=req.name,
        handler=printer
    )

    return {"status": "replayed"}


# =========================
# SERVER START
# =========================

def run_api():
    import uvicorn

    uvicorn.run(
        "api.server:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info"
    )