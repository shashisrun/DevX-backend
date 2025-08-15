from functools import wraps
from typing import Iterable

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.project import Project
from src.models.enums import ProjectStatus
from src.services.ws_manager import ws_broadcast

ALLOWED_TRANSITIONS = {
    ProjectStatus.NEW: {ProjectStatus.DISCOVERY},
    ProjectStatus.DISCOVERY: {ProjectStatus.PLANNING},
    ProjectStatus.PLANNING: {ProjectStatus.DESIGN},
    ProjectStatus.DESIGN: {ProjectStatus.BUILD},
    ProjectStatus.BUILD: {ProjectStatus.TEST},
    ProjectStatus.TEST: {ProjectStatus.REVIEW, ProjectStatus.TEST_FAIL},
    ProjectStatus.REVIEW: {ProjectStatus.DEPLOY},
    ProjectStatus.DEPLOY: {ProjectStatus.MONITOR},
    ProjectStatus.MONITOR: {ProjectStatus.DONE},
    ProjectStatus.TEST_FAIL: {ProjectStatus.ROLLBACK, ProjectStatus.TEST},
    ProjectStatus.ROLLBACK: {ProjectStatus.BUILD},
}


def enforce_state(*, from_: Iterable[ProjectStatus], to: ProjectStatus):
    """Decorator ensuring a project is in an allowed state before executing."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            project: Project = kwargs.get("project")
            session: AsyncSession = kwargs.get("session")
            if project is None or session is None:
                raise RuntimeError("project and session must be provided")
            if project.status not in from_:
                raise HTTPException(status_code=409, detail="Illegal state transition")
            result = await func(*args, **kwargs)
            await advance_state(session, project, to)
            return result

        return wrapper

    return decorator


def _allowed(current: ProjectStatus, target: ProjectStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


async def advance_state(session: AsyncSession, project: Project, to_status: ProjectStatus) -> Project:
    if not _allowed(project.status, to_status):
        raise HTTPException(status_code=409, detail="Illegal state transition")
    project.status = to_status
    session.add(project)
    await session.commit()
    await session.refresh(project)
    await ws_broadcast(
        {
            "type": "state.changed",
            "project_id": project.id,
            "payload": {"status": project.status.value},
        }
    )
    return project


async def get_project(session: AsyncSession, project_id: int) -> Project:
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
