from fastapi import APIRouter
from ..services.task_queue import diff_task

router = APIRouter()

@router.post("/api/projects/{id}/diff")
async def compute_diff(id: int, file_a: str, file_b: str):
    task = diff_task.delay(id, file_a, file_b)
    return {"task_id": task.id, "status": "diff started", "project_id": id, "file_a": file_a, "file_b": file_b}
