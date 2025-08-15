from fastapi import APIRouter
from ..services.task_queue import file_task

router = APIRouter()

@router.post("/api/projects/{id}/file")
async def file_ops(id: int, path: str, content: str = None):
    task = file_task.delay(id, path, content)
    return {"task_id": task.id, "status": "file op started", "project_id": id, "path": path}
