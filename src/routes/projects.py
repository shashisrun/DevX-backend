from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..db import get_session
from ..models.enums import ProjectStatus
from ..models.project import Project
from ..services.agent_service import AgentService
from ..services.task_queue import index_task
from ..utils.state_machine import advance_state, get_project

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/", response_model=List[Project])
async def list_projects(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project))
    return result.scalars().all()

@router.post("/", response_model=Project)
async def create_project(project: Project, session: AsyncSession = Depends(get_session)):
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project

@router.post("/{project_id}/index")
async def trigger_index(project_id: int):
    task = index_task.delay(project_id)
    return {"task_id": task.id, "status": "started"}

@router.post("/{project_id}/agent")
async def run_agent(project_id: int, payload: dict):
    agent = AgentService()
    result = await agent.run_agent_task(payload)
    return result


class StatusUpdate(BaseModel):
    status: ProjectStatus


@router.post("/{project_id}/advance", response_model=Project)
async def advance_project(
    project_id: int,
    update: StatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    project = await advance_state(session, project, update.status)
    return project
