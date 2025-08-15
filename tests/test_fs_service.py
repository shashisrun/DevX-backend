import pytest
from src.services.fs_service import FSService


@pytest.mark.asyncio
async def test_write_and_read_round_trip(tmp_path):
    service = FSService(root=tmp_path)
    content = b"hello world"
    file_path = tmp_path / "test.txt"

    meta = await service.write_file(str(file_path), content)
    assert meta.size == len(content)

    data = await service.read_file(str(file_path))
    assert bytes(data) == content
    assert str(file_path.resolve()) in service.meta

