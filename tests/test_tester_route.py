import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlmodel import select

from src.main import app
from src.db import async_session
from src.models.artifact import Artifact


@pytest.mark.asyncio
async def test_test_route_fail_then_pass_with_loop(monkeypatch):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # create project and progress to BUILD
        create = await ac.post("/api/projects/", json={"name": "qa"})
        pid = create.json()["id"]
        await ac.post(f"/api/projects/{pid}/init", json={"features": ["feat"]})
        await ac.post(f"/api/projects/{pid}/plan")
        await ac.post(f"/api/projects/{pid}/design")

    # open WS to capture qa.report
    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/{pid}") as ws:
            # Force test failure
            from src.services import test_service as ts

            async def fail_runner(self, project_id: int):
                return {"passed": False, "coverage": 10.0, "summary": "failing"}

            monkeypatch.setattr(ts.TestService, "run_tests", fail_runner, raising=False)
            resp = client.post(f"/api/projects/{pid}/test")
            assert resp.status_code == 200
            assert resp.json()["status"] == "TEST_FAIL"
            # expect qa.report event
            evt = ws.receive_json()
            assert evt["type"] in ("state.changed", "qa.report")
            seen_report = evt["type"] == "qa.report"
            for _ in range(4):
                if seen_report:
                    break
                evt = ws.receive_json()
                if evt["type"] == "qa.report":
                    seen_report = True
            assert seen_report

    # verify report stored
    async with async_session() as session:
        arts = (await session.execute(select(Artifact).where(Artifact.project_id == pid).where(Artifact.kind == "test_report"))).scalars().all()
        assert len(arts) >= 1

    # Loop back to BUILD and pass
    with TestClient(app) as client:
        # TEST_FAIL -> ROLLBACK -> BUILD
        rb = client.post(f"/api/projects/{pid}/advance", json={"status": "ROLLBACK"})
        assert rb.status_code == 200
        assert rb.json()["status"] == "ROLLBACK"
        build = client.post(f"/api/projects/{pid}/advance", json={"status": "BUILD"})
        assert build.status_code == 200
        assert build.json()["status"] == "BUILD"

        # Now force pass
        from src.services import test_service as ts

        async def pass_runner(self, project_id: int):
            return {"passed": True, "coverage": 70.0, "summary": "ok"}

        from importlib import reload
        monkeypatch.setattr(ts.TestService, "run_tests", pass_runner, raising=False)
        with client.websocket_connect(f"/ws/{pid}") as ws:
            resp2 = client.post(f"/api/projects/{pid}/test")
            assert resp2.status_code == 200
            assert resp2.json()["status"] == "REVIEW"
            # expect qa.report
            evt = ws.receive_json()
            assert evt["type"] in ("state.changed", "qa.report")
