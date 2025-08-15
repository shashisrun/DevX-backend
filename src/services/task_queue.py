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
def diff_task(project_id: int, before: str, after: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(diff_service.compute_diff(before, after))

@celery_app.task
def file_task(project_id: int, path: str, content: str | None = None):
    loop = asyncio.get_event_loop()
    if content is not None:
        return loop.run_until_complete(fs_service.write_file(path, content.encode("utf-8")))
    else:
        data = loop.run_until_complete(fs_service.read_file(path))
        return data.tobytes().decode("utf-8")


# Build DAG related tasks


@celery_app.task(name="index_repo")
def index_repo(job_id: int, project_id: int, params: dict | None = None):
    """Index the repository for a project."""
    return asyncio.run(index_service.build_index(project_id))


@celery_app.task(name="implement_endpoints")
def implement_endpoints(job_id: int, project_id: int, params: dict | None = None):
    """Placeholder task ensuring route stubs and tests exist."""
    return {"status": "ok"}


@celery_app.task(name="write_tests")
def write_tests(job_id: int, project_id: int, params: dict | None = None):
    """Placeholder task that would add missing skeleton tests."""
    return {"status": "ok"}


@celery_app.task(name="configure_ci")
def configure_ci(job_id: int, project_id: int, params: dict | None = None):
    """Placeholder task ensuring a CI workflow exists."""
    return {"status": "ok"}
