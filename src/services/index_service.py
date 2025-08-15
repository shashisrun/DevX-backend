import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from sqlmodel import select, delete

from ..db import async_session
from ..models import FileMeta

try:  # pragma: no cover - optional dependency
    import indexer_rs
except Exception:  # pragma: no cover
    indexer_rs = None

ProgressCallback = Callable[[int, str], Any]


class IndexService:
    async def build_index(
        self, project_id: int, progress_cb: Optional[ProgressCallback] = None
    ) -> dict:
        """(Re)build index incrementally for a project."""

        if indexer_rs is None:
            return {}

        root = Path(f"/projects/{project_id}")
        if not root.exists():
            return {}

        loop = asyncio.get_event_loop()

        async with async_session() as session:
            existing = await session.execute(
                select(FileMeta).where(FileMeta.project_id == project_id)
            )
            meta_map = {m.path: m for m in existing.scalars().all()}

            files_on_disk = [p for p in root.rglob("*") if p.is_file()]
            changed = []
            for file_path in files_on_disk:
                rel = str(file_path.relative_to(root))
                stat = file_path.stat()
                meta = meta_map.get(rel)
                if meta and meta.size == stat.st_size and meta.mtime == stat.st_mtime:
                    continue
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()
                changed.append((file_path, rel, stat, file_hash))

            total = len(changed)
            for idx, (file_path, rel, stat, file_hash) in enumerate(changed, start=1):
                await loop.run_in_executor(None, indexer_rs.build_index, str(file_path))
                meta = meta_map.get(rel)
                now = datetime.utcnow()
                if meta:
                    meta.size = stat.st_size
                    meta.mtime = stat.st_mtime
                    meta.hash = file_hash
                    meta.last_indexed_at = now
                else:
                    meta = FileMeta(
                        project_id=project_id,
                        path=rel,
                        size=stat.st_size,
                        mtime=stat.st_mtime,
                        hash=file_hash,
                        lang=file_path.suffix.lstrip(".") or None,
                        symbols_count=0,
                        last_indexed_at=now,
                    )
                session.add(meta)
                await session.commit()
                if progress_cb:
                    percent = int(idx * 100 / total) if total else 100
                    if asyncio.iscoroutinefunction(progress_cb):
                        await progress_cb(percent, rel)
                    else:  # pragma: no cover - sync callbacks
                        progress_cb(percent, rel)

            current_paths = {str(p.relative_to(root)) for p in files_on_disk}
            stale = set(meta_map.keys()) - current_paths
            for rel in stale:
                await session.execute(
                    delete(FileMeta).where(
                        FileMeta.project_id == project_id, FileMeta.path == rel
                    )
                )
            if stale:
                await session.commit()

        return {"indexed": total}

    async def search_index(
        self, project_id: int, query: str, lang: str | None = None, path: str | None = None
    ) -> Any:
        if indexer_rs is None:
            return []
        loop = asyncio.get_event_loop()
        search_q = query
        if lang:
            search_q += f" lang:{lang}"
        if path:
            search_q += f" path:{path}"
        result = await loop.run_in_executor(None, indexer_rs.search_index, search_q)
        return memoryview(result) if hasattr(result, "__buffer__") else result
