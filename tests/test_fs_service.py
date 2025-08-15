import pytest
from src.services.fs_service import FSService


@pytest.mark.asyncio
async def test_read_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    service = FSService()
    result = await service.read_file(str(file_path))
    assert result == "hello"
