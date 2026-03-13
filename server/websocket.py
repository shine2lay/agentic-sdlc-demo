"""WebSocket endpoint — relays run events to frontend in real-time."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select

from server.database import engine
from server.models import RunEvent

logger = logging.getLogger(__name__)

ws_router = APIRouter()

# Active WebSocket connections per run_id
_connections: dict[str, set[WebSocket]] = {}


async def broadcast_to_run(run_id: str, message: dict) -> None:
    """Send a message to all WebSocket clients watching a run."""
    clients = _connections.get(run_id, set())
    dead = set()
    for ws in clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    clients -= dead


@ws_router.websocket("/ws/{run_id}")
async def run_websocket(websocket: WebSocket, run_id: str):
    await websocket.accept()

    if run_id not in _connections:
        _connections[run_id] = set()
    _connections[run_id].add(websocket)

    # Send existing events as initial snapshot
    with Session(engine) as session:
        events = session.exec(
            select(RunEvent)
            .where(RunEvent.run_id == run_id)
            .order_by(RunEvent.created_at)
        ).all()
        await websocket.send_json({
            "type": "snapshot",
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "data": json.loads(e.data) if e.data else {},
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
            ],
        })

    # Poll for new events (will be replaced with pg NOTIFY later)
    last_event_id = events[-1].id if events else 0

    try:
        while True:
            await asyncio.sleep(1)
            with Session(engine) as session:
                new_events = session.exec(
                    select(RunEvent)
                    .where(RunEvent.run_id == run_id)
                    .where(RunEvent.id > last_event_id)
                    .order_by(RunEvent.created_at)
                ).all()
                for e in new_events:
                    await websocket.send_json({
                        "type": "event",
                        "event_type": e.event_type,
                        "data": json.loads(e.data) if e.data else {},
                        "created_at": e.created_at.isoformat(),
                    })
                    last_event_id = e.id
    except WebSocketDisconnect:
        _connections[run_id].discard(websocket)
        if not _connections[run_id]:
            del _connections[run_id]
