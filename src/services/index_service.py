import asyncio
from typing import Any

try:
    import indexer_rs
except Exception:  # pragma: no cover - optional dependency
    indexer_rs = None

class IndexService:
    async def build_index(self, project_id: int) -> Any:
        if indexer_rs is None:
            return {}
        loop = asyncio.get_event_loop()
        path = f"/projects/{project_id}"
        result = await loop.run_in_executor(None, indexer_rs.build_index, path)
        return memoryview(result) if hasattr(result, "__buffer__") else result

    async def search_index(self, query: str) -> Any:
        if indexer_rs is None:
            return {}
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, indexer_rs.search_index, query)
        return memoryview(result) if hasattr(result, "__buffer__") else result
