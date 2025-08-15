import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_requirements_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/projects/", json={"name": "demo"})
        project_id = create.json()["id"]
        resp = await ac.post(
            f"/api/projects/{project_id}/init", json={"foo": "bar"}
        )
        assert resp.status_code == 422
        assert "features" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_artifact_listing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/projects/", json={"name": "demo"})
        pid = create.json()["id"]
        await ac.post(f"/api/projects/{pid}/init", json={"features": ["one"]})
        await ac.post(f"/api/projects/{pid}/plan")
        reqs = await ac.get(f"/api/projects/{pid}/artifacts", params={"kind": "requirements"})
        assert reqs.status_code == 200
        data = reqs.json()
        assert len(data) == 1
        assert data[0]["kind"] == "requirements"
        assert "features" in data[0]["content"]
        plan = await ac.get(f"/api/projects/{pid}/artifacts", params={"kind": "plan"})
        assert plan.status_code == 200
        pdata = plan.json()
        assert len(pdata) == 1
        assert pdata[0]["kind"] == "plan"
        assert "dag" in pdata[0]["content"]
