from fastapi.testclient import TestClient
from src.main import app
from src.services.ws_manager import ws_broadcast


def test_ws_broadcast_envelope():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as websocket:
            event = {"type": "job.started", "project_id": 1, "payload": {"node": 0}}
            client.portal.call(ws_broadcast, event)
            data = websocket.receive_json()
            assert data["type"] == "job.started"
            assert data["project_id"] == 1
            assert data["payload"] == {"node": 0}
            assert "ts" in data
            assert "trace_id" in data
