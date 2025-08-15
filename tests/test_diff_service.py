import pytest
from src.services.diff_service import DiffService

@pytest.mark.asyncio
async def test_compute_diff():
    service = DiffService()
    result = await service.compute_diff("a", "b")
    assert result is not None
