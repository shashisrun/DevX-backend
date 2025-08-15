import asyncio
import hashlib
import mmap
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import fsops_rs
except Exception:  # pragma: no cover
    fsops_rs = None


@dataclass
class FileMeta:
    """Metadata about a file on disk."""

    size: int
    mtime: float
    hash: str


class FSService:
    """File system helper with safe, atomic operations."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path.cwd()).resolve()
        self.meta: Dict[str, FileMeta] = {}

    def _safe_path(self, path: str) -> Path:
        """Return an absolute path ensured to be within the root directory."""
        from fastapi import HTTPException
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        p = p.resolve()
        try:
            p.relative_to(self.root)
        except ValueError as exc:  # pragma: no cover - simple guard
            # Translate traversal attempts to HTTP 403 for routes using FSService
            raise HTTPException(status_code=403, detail="Path escapes root directory") from exc
        return p

    async def read_file(self, path: str) -> Any:
        path_obj = self._safe_path(path)
        loop = asyncio.get_event_loop()

        def _read():
            if fsops_rs is not None:  # pragma: no cover - exercised in rust impl
                result = fsops_rs.read_file(str(path_obj))
                return memoryview(result) if hasattr(result, "__buffer__") else result
            with open(path_obj, "rb") as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                return memoryview(mm)

        return await loop.run_in_executor(None, _read)

    async def write_file(self, path: str, content: bytes) -> FileMeta:
        path_obj = self._safe_path(path)
        loop = asyncio.get_event_loop()

        def _write() -> FileMeta:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            if fsops_rs is not None:  # pragma: no cover - exercised in rust impl
                fsops_rs.write_file(str(path_obj), content)
            else:
                with tempfile.NamedTemporaryFile(dir=path_obj.parent, delete=False) as tmp:
                    tmp.write(content)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    tmp_path = Path(tmp.name)
                os.replace(tmp_path, path_obj)
                dir_fd = os.open(
                    path_obj.parent,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
                )
                try:  # ensure rename is durable
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)

            stat = path_obj.stat()
            file_hash = hashlib.sha256(content).hexdigest()
            meta = FileMeta(size=stat.st_size, mtime=stat.st_mtime, hash=file_hash)
            self.meta[str(path_obj)] = meta
            return meta

        return await loop.run_in_executor(None, _write)
