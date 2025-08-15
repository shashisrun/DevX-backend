import pytest
from src.services.index_service import IndexService

@pytest.mark.asyncio
async def test_build_index():
    service = IndexService()
    result = await service.build_index(1)
    assert result is not None
