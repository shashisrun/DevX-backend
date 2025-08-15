import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_diff_endpoint_returns_hunks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/projects/1/diff",
            json={"before": "hello\nworld\n", "after": "hello\nthere\nworld\n"},
        )
    assert resp.status_code == 200
    assert resp.json()["hunks"] == [
        {
            "old_start": 1,
            "old_lines": 2,
            "new_start": 1,
            "new_lines": 3,
            "lines": [" hello", "+there", " world"],
        }
    ]
