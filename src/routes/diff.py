from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.diff_service import DiffService
from ..services.fs_service import FSService


router = APIRouter()


class DiffRequest(BaseModel):
    before: Optional[str] = None
    after: Optional[str] = None
    before_path: Optional[str] = None
    after_path: Optional[str] = None


@router.post("/api/projects/{id}/diff")
async def compute_diff(id: int, payload: DiffRequest):  # noqa: ARG001 - id for route parity
    fs = FSService()
    diff = DiffService()

    if payload.before_path:
        before_bytes = await fs.read_file(payload.before_path)
        before = before_bytes.tobytes().decode("utf-8")
    else:
        before = payload.before or ""

    if payload.after_path:
        after_bytes = await fs.read_file(payload.after_path)
        after = after_bytes.tobytes().decode("utf-8")
    else:
        after = payload.after or ""

    if before is None or after is None:
        raise HTTPException(status_code=400, detail="Both before and after content required")

    hunks = await diff.compute_diff(before, after)
    return {"project_id": id, "hunks": hunks}

