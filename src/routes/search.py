from fastapi import APIRouter
from typing import Optional

from ..services.index_service import IndexService

router = APIRouter()
index_service = IndexService()


@router.get("/api/projects/{id}/search")
async def search_project(
    id: int, q: str, lang: Optional[str] = None, path: Optional[str] = None
):
    hits = await index_service.search_index(id, q, lang=lang, path=path)
    return {"project_id": id, "query": q, "hits": hits}
