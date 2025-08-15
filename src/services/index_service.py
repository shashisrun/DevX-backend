import asyncio
import indexer_rs
from typing import Any

class IndexService:
    async def build_index(self, project_id: int) -> Any:
        # Simulate async call to Rust
        loop = asyncio.get_event_loop()
        # Replace with actual project path lookup
        path = f"/projects/{project_id}"
        result = await loop.run_in_executor(None, indexer_rs.build_index, path)
        return memoryview(result) if hasattr(result, "__buffer__") else result

    async def search_index(self, query: str) -> Any:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, indexer_rs.search_index, query)
        return memoryview(result) if hasattr(result, "__buffer__") else result
