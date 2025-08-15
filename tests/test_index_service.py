from pathlib import Path

import pytest

from src.services.index_service import IndexService


@pytest.mark.asyncio
async def test_incremental_indexing(monkeypatch):
    project_dir = Path("/projects/1")
    project_dir.mkdir(parents=True, exist_ok=True)
    file_path = project_dir / "file.txt"
    file_path.write_text("content")

    calls = []

    class DummyIndexer:
        def build_index(self, path: str):  # pragma: no cover - stub
            calls.append(path)

    monkeypatch.setattr(
        "src.services.index_service.indexer_rs", DummyIndexer()
    )

    service = IndexService()
    await service.build_index(1)
    assert len(calls) == 1

    await service.build_index(1)
    assert len(calls) == 1  # unchanged file skipped
