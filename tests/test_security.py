import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import select

from src.main import app
from src.db import async_session
from src.models.artifact import Artifact
from src.services.sandbox import ShellSandbox


@pytest.mark.asyncio
async def test_artifact_path_traversal_is_forbidden():
    # Insert an artifact with a malicious uri and try to fetch via API
    async with async_session() as session:
        art = Artifact(project_id=9999, kind="blob", uri="../../../../etc/passwd")
        session.add(art)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # list artifacts for project id 9999 will try to read content since content is None
        resp = await ac.get("/api/projects/9999/artifacts")
        # Should not be 500; should forbid
        assert resp.status_code == 403


def test_shell_sandbox_rejects_disallowed_commands():
    sb = ShellSandbox(allowlist={"echo"})
    with pytest.raises(Exception):
        # curl is not allowed
        import asyncio
        asyncio.run(sb.run(["curl", "http://example.com"]))

    # allowed command works
    import asyncio
    result = asyncio.run(sb.run(["echo", "ok"]))
    assert result.code == 0
    assert "ok" in result.stdout
