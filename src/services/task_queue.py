from celery import Celery
from ..config import settings
from .index_service import IndexService
from .diff_service import DiffService
from .fs_service import FSService
import asyncio

celery_app = Celery(
    "devinx",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

index_service = IndexService()
diff_service = DiffService()
fs_service = FSService()

@celery_app.task
def index_task(project_id: int):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(index_service.build_index(project_id))

@celery_app.task
def search_task(project_id: int, query: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(index_service.search_index(query))

@celery_app.task
def diff_task(project_id: int, file_a: str, file_b: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(diff_service.compute_diff(file_a, file_b))

@celery_app.task
def file_task(project_id: int, path: str, content: str = None):
    loop = asyncio.get_event_loop()
    if content:
        return loop.run_until_complete(fs_service.write_file(path, content))
    else:
        return loop.run_until_complete(fs_service.read_file(path))
