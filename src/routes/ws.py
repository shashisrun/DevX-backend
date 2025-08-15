from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog
import asyncio

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger = structlog.get_logger()
    try:
        await websocket.send_text("WebSocket connection established.")
        while True:
            data = await websocket.receive_text()
            logger.info("ws.received", data=data)
            # Simulate streaming logs/progress
            for i in range(3):
                await asyncio.sleep(1)
                msg = f"Progress {i+1}/3 for: {data}"
                logger.info("ws.progress", progress=msg)
                await websocket.send_text(msg)
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("ws.disconnect")
