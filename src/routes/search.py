from fastapi import APIRouter
from ..services.task_queue import search_task

router = APIRouter()

@router.post("/api/projects/{id}/search")
async def search_project(id: int, query: str):
    task = search_task.delay(id, query)
    return {"task_id": task.id, "status": "search started", "project_id": id, "query": query}
