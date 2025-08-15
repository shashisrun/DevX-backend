import asyncio
import diff_rs
from typing import Any

class DiffService:
    async def compute_diff(self, file_a: str, file_b: str) -> Any:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, diff_rs.compute_diff, file_a, file_b)
        return memoryview(result) if hasattr(result, "__buffer__") else result
