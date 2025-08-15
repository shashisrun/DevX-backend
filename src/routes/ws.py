from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int):
    await manager.connect(websocket, project_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
