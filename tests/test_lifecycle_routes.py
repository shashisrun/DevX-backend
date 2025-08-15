import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import select

from src.main import app
from src.db import async_session
from src.models.artifact import Artifact


@pytest.mark.asyncio
async def test_lifecycle_basic():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/projects/", json={"name": "demo"})
        assert create.status_code == 200
        project_id = create.json()["id"]

        init_resp = await ac.post(
            f"/api/projects/{project_id}/init", json={"features": ["value"]}
        )
        assert init_resp.status_code == 200
        assert init_resp.json()["status"] == "DISCOVERY"
        async with async_session() as session:
            result = await session.execute(
                select(Artifact).where(Artifact.project_id == project_id)
            )
            arts = result.scalars().all()
            assert any(a.kind == "requirements" for a in arts)

        plan_resp = await ac.post(f"/api/projects/{project_id}/plan")
        assert plan_resp.status_code == 200
        assert plan_resp.json()["status"] == "PLANNING"
        async with async_session() as session:
            result = await session.execute(
                select(Artifact).where(Artifact.project_id == project_id)
            )
            arts = result.scalars().all()
            assert any(a.kind == "plan" for a in arts)

        approve_resp = await ac.post(
            f"/api/projects/{project_id}/approve", params={"gate": "PLANNING"}
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "DESIGN"
