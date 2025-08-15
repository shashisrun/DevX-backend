import os
import pytest
from src.services.index_service import IndexService


@pytest.mark.asyncio
async def test_build_index(tmp_path):
    project_dir = "/projects/1"
    os.makedirs(project_dir, exist_ok=True)
    (tmp_path / "file.txt").write_text("content")
    # copy file into expected project path
    import shutil
    shutil.copy(tmp_path / "file.txt", os.path.join(project_dir, "file.txt"))
    service = IndexService()
    result = await service.build_index(1)
    assert result is not None
