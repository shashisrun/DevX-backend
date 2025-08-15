from fastapi import WebSocket
from typing import Dict, List
from collections import defaultdict
import json
from datetime import datetime, timezone
from uuid import uuid4

from ..utils.schema import validate_schema


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, project_id: int) -> None:
        await websocket.accept()
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        for project_id, conns in list(self.active_connections.items()):
            if websocket in conns:
                conns.remove(websocket)
                if not conns:
                    del self.active_connections[project_id]
                break

    async def broadcast(self, project_id: int, message: dict) -> None:
        data = json.dumps(message)
        for connection in list(self.active_connections.get(project_id, [])):
            try:
                await connection.send_text(data)
            except Exception:
                self.disconnect(connection)


async def ws_broadcast(event: dict) -> None:
    if "ts" not in event:
        event["ts"] = datetime.now(timezone.utc).isoformat()
    if "trace_id" not in event:
        event["trace_id"] = uuid4().hex
    validate_schema(event, "events")
    project_id = event.get("project_id")
    if project_id is None:
        raise ValueError("event must include project_id")
    await manager.broadcast(project_id, event)


manager = ConnectionManager()
