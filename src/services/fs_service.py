import asyncio
from typing import Any
try:
    import fsops_rs
except Exception:  # pragma: no cover - optional dependency
    fsops_rs = None

class FSService:
    async def read_file(self, path: str) -> Any:
        loop = asyncio.get_event_loop()
        if fsops_rs is None:
            import pathlib

            result = await loop.run_in_executor(None, pathlib.Path(path).read_text)
            return result
        result = await loop.run_in_executor(None, fsops_rs.read_file, path)
        return memoryview(result) if hasattr(result, "__buffer__") else result

    async def write_file(self, path: str, content: str) -> Any:
        loop = asyncio.get_event_loop()
        if fsops_rs is None:
            import pathlib

            result = await loop.run_in_executor(None, pathlib.Path(path).write_text, content)
            return result
        result = await loop.run_in_executor(None, fsops_rs.write_file, path, content)
        return result
