from fastapi import APIRouter
from ..services.task_queue import index_task

router = APIRouter()

@router.post("/api/projects/{id}/index")
async def trigger_index(id: int):
    task = index_task.delay(id)
    return {"task_id": task.id, "status": "indexing started", "project_id": id}
