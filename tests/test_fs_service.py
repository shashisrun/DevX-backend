import pytest
from src.services.fs_service import FSService

@pytest.mark.asyncio
async def test_read_file():
    service = FSService()
    result = await service.read_file("/tmp/test.txt")
    assert result is not None
