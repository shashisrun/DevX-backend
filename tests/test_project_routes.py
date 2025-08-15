import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_advance_project_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # create a new project
        create_resp = await ac.post("/api/projects/", json={"name": "demo"})
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "NEW"

        # advance to DISCOVERY
        advance_resp = await ac.post(
            f"/api/projects/{project_id}/advance", json={"status": "DISCOVERY"}
        )
        assert advance_resp.status_code == 200
        assert advance_resp.json()["status"] == "DISCOVERY"

        # invalid transition back to NEW should fail
        invalid_resp = await ac.post(
            f"/api/projects/{project_id}/advance", json={"status": "NEW"}
        )
        assert invalid_resp.status_code == 409
