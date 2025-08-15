import pytest
from src.services.diff_service import DiffService


@pytest.mark.asyncio
async def test_compute_diff_known_sample():
    service = DiffService()
    before = "hello\nworld\n"
    after = "hello\nthere\nworld\n"
    hunks = await service.compute_diff(before, after)
    assert hunks == [
        {
            "old_start": 1,
            "old_lines": 2,
            "new_start": 1,
            "new_lines": 3,
            "lines": [" hello", "+there", " world"],
        }
    ]

