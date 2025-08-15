import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from src.main import app
from src.db import async_session
from src.models.artifact import Artifact
from sqlmodel import select


@pytest.mark.asyncio
async def test_init_triggers_planner_and_plan_artifact():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/projects/", json={"name": "auto"})
        pid = create.json()["id"]
        init = await ac.post(f"/api/projects/{pid}/init", json={"features": ["x"]})
        assert init.status_code == 200
        assert init.json()["status"] == "DISCOVERY"
        # plan should already exist
        async with async_session() as session:
            result = await session.execute(select(Artifact).where(Artifact.project_id == pid).where(Artifact.kind == "plan"))
            arts = result.scalars().all()
            assert len(arts) == 1


@pytest.mark.asyncio
async def test_plan_uses_existing_and_advances_state():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/projects/", json={"name": "auto2"})
        pid = create.json()["id"]
        await ac.post(f"/api/projects/{pid}/init", json={"features": ["y"]})
        # count plans before /plan
        async with async_session() as session:
            before = (await session.execute(select(Artifact).where(Artifact.project_id == pid).where(Artifact.kind == "plan"))).scalars().all()
            n_before = len(before)
        plan = await ac.post(f"/api/projects/{pid}/plan")
        assert plan.status_code == 200
        assert plan.json()["status"] == "PLANNING"
        async with async_session() as session:
            after = (await session.execute(select(Artifact).where(Artifact.project_id == pid).where(Artifact.kind == "plan"))).scalars().all()
            assert len(after) == n_before  # no new plan created


def test_design_emits_job_events_and_creates_contracts(monkeypatch):
    # disable approval gate for this test
    monkeypatch.setenv("REQUIRE_APPROVAL_PLANNING", "false")
    with TestClient(app) as client:
        # create project and progress to PLANNING
        resp = client.post("/api/projects/", json={"name": "auto3"})
        pid = resp.json()["id"]
        client.post(f"/api/projects/{pid}/init", json={"features": ["z"]})
        client.post(f"/api/projects/{pid}/plan")
        # listen for WS events while calling /design
        with client.websocket_connect(f"/ws/{pid}") as websocket:
            dresp = client.post(f"/api/projects/{pid}/design")
            assert dresp.status_code == 200
            assert dresp.json()["status"] == "BUILD"
            # first WS message should be job.started for design
            evt = websocket.receive_json()
            assert evt["type"] in ("job.started", "state.changed")
            # Drain messages until we see job.completed for design
            seen_completed = (evt["type"] == "job.completed")
            for _ in range(5):
                if seen_completed:
                    break
                evt = websocket.receive_json()
                if evt["type"] == "job.completed":
                    seen_completed = True
            assert seen_completed
        # verify contracts saved
        contracts = client.get(f"/api/projects/{pid}/contracts").json()
        assert "openapi" in contracts
        assert "events" in contracts


def test_design_requires_approval_when_gate_enabled(monkeypatch):
    monkeypatch.setenv("REQUIRE_APPROVAL_PLANNING", "true")
    with TestClient(app) as client:
        resp = client.post("/api/projects/", json={"name": "auto4"})
        pid = resp.json()["id"]
        client.post(f"/api/projects/{pid}/init", json={"features": ["z"]})
        client.post(f"/api/projects/{pid}/plan")
        # direct design should fail due to gate
        blocked = client.post(f"/api/projects/{pid}/design")
        assert blocked.status_code == 409
        # approve and then design should succeed
        ok = client.post(f"/api/projects/{pid}/approve", params={"gate": "PLANNING"})
        assert ok.status_code == 200
        assert ok.json()["status"] == "DESIGN"
        done = client.post(f"/api/projects/{pid}/design")
        assert done.status_code == 200
        assert done.json()["status"] == "BUILD"

