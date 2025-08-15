import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlmodel import select

from src.main import app
from src.db import async_session
from src.models.artifact import Artifact


@pytest.mark.asyncio
async def test_deploy_success_emits_events_and_saves_runbook(monkeypatch):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/projects/", json={"name": "deploydemo"})
        pid = create.json()["id"]
        await ac.post(f"/api/projects/{pid}/init", json={"features": ["feat"]})
        await ac.post(f"/api/projects/{pid}/plan")
        await ac.post(f"/api/projects/{pid}/design")
        # make tests pass to reach REVIEW
        from src.services import test_service as ts

        async def pass_runner(self, project_id: int):
            return {"passed": True}

        monkeypatch.setattr(ts.TestService, "run_tests", pass_runner, raising=False)
        trest = await ac.post(f"/api/projects/{pid}/test")
        assert trest.json()["status"] == "REVIEW"

    # monkeypatch deploy runner to be deterministic
    from src.services import deploy_service as ds

    class FakeRunner(ds.DeployRunner):
        async def build_image(self, project):
            return "demo:latest"

        async def generate_manifests(self, project, kind: str = "compose"):
            return "version: '3'\nservices: {}\n"

        async def run_smoke(self, image_ref: str):
            return True

    monkeypatch.setattr(ds.DeployService, "__init__", lambda self, runner=None, broadcaster=None: None, raising=False)
    # inject attributes expected by service methods
    def _svc_init(self, runner=None, broadcaster=None):
        self.runner = FakeRunner()
        from src.services.ws_manager import ws_broadcast
        self.broadcaster = ws_broadcast

    monkeypatch.setattr(ds.DeployService, "__init__", _svc_init, raising=False)

    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/{pid}") as ws:
            d = client.post(f"/api/projects/{pid}/deploy")
            assert d.status_code == 200
            assert d.json()["status"] == "MONITOR"
            # expect deploy.status
            evt = ws.receive_json()
            assert evt["type"] in ("state.changed", "deploy.status")
            seen_deploy = evt["type"] == "deploy.status"
            for _ in range(5):
                if seen_deploy:
                    break
                evt = ws.receive_json()
                if evt["type"] == "deploy.status":
                    seen_deploy = True
            assert seen_deploy

    # verify runbook artifact exists
    async with async_session() as session:
        arts = (await session.execute(select(Artifact).where(Artifact.project_id == pid).where(Artifact.kind == "runbook"))).scalars().all()
        assert len(arts) == 1
        assert "Runbook" in arts[0].content

