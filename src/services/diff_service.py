import asyncio
from typing import Any

try:
    import diff_rs
except Exception:  # pragma: no cover - optional dependency
    diff_rs = None

class DiffService:
    async def compute_diff(self, file_a: str, file_b: str) -> Any:
        if diff_rs is None:
            return ""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, diff_rs.compute_diff, file_a, file_b)
        return memoryview(result) if hasattr(result, "__buffer__") else result
