import asyncio
import fsops_rs
from typing import Any

class FSService:
    async def read_file(self, path: str) -> Any:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, fsops_rs.read_file, path)
        return memoryview(result) if hasattr(result, "__buffer__") else result

    async def write_file(self, path: str, content: str) -> Any:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, fsops_rs.write_file, path, content)
        return result
