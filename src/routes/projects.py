from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from ..db import get_session
from ..models.enums import ProjectStatus
from ..models.project import Project
from ..models.artifact import Artifact
from ..services.agent_service import AgentService
from ..services.task_queue import index_task
from ..utils.state_machine import advance_state, get_project, enforce_state
from ..services.ws_manager import manager
from uuid import uuid4
from ..services.fs_service import FSService
from ..utils.schema import validate_schema

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


@router.post("/{project_id}/init", response_model=Project)
async def init_project(
    project_id: int,
    requirements: dict,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    validate_schema(requirements, "requirements")
    await _init(project=project, session=session, requirements=requirements)
    return project


@router.post("/{project_id}/plan", response_model=Project)
async def plan_project(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    await _plan(project=project, session=session)
    return project


@router.post("/{project_id}/approve", response_model=Project)
async def approve_project(
    project_id: int,
    gate: ProjectStatus,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    await _approve(project=project, session=session, gate=gate)
    return project


@router.post("/{project_id}/design", response_model=Project)
async def design_project(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    await _design(project=project, session=session)
    return project


@router.post("/{project_id}/build", response_model=Project)
async def build_project(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    if project.status != ProjectStatus.BUILD:
        raise HTTPException(status_code=409, detail="Illegal state transition")
    await _build(project=project, session=session)
    return project


@router.post("/{project_id}/test", response_model=Project)
async def test_project(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    await _test(project=project, session=session)
    project = await advance_state(session, project, ProjectStatus.REVIEW)
    return project


@router.post("/{project_id}/deploy", response_model=Project)
async def deploy_project(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    await _deploy(project=project, session=session)
    project = await advance_state(session, project, ProjectStatus.MONITOR)
    return project


@router.get("/{project_id}/artifacts")
async def list_artifacts(
    project_id: int,
    kind: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Artifact).where(Artifact.project_id == project_id)
    if kind:
        stmt = stmt.where(Artifact.kind == kind)
    result = await session.execute(stmt)
    artifacts = result.scalars().all()
    fs = FSService()
    resp = []
    for art in artifacts:
        content = art.content
        if not content and art.uri:
            content = await fs.read_file(art.uri)
        resp.append(
            {
                "id": art.id,
                "kind": art.kind,
                "content": content,
            }
        )
    return resp


@router.get("/{project_id}/contracts")
async def get_contracts(project_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Artifact).where(Artifact.project_id == project_id).where(
        Artifact.kind.in_(["openapi", "events"])
    )
    result = await session.execute(stmt)
    artifacts = result.scalars().all()
    fs = FSService()
    contracts = {}
    for art in artifacts:
        content = art.content
        if not content and art.uri:
            content = await fs.read_file(art.uri)
        contracts[art.kind] = content
    return contracts


async def _save_artifact(session: AsyncSession, project: Project, kind: str, content: str) -> Artifact:
    fs = FSService()
    artifact = Artifact(project_id=project.id, kind=kind)
    if content and len(content) > 1000:
        path = f"artifacts/{uuid4().hex}.txt"
        await fs.write_file(path, content)
        artifact.uri = path
    else:
        artifact.content = content
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)
    return artifact


@enforce_state(from_=[ProjectStatus.NEW], to=ProjectStatus.DISCOVERY)
async def _init(*, project: Project, session: AsyncSession, requirements: dict):
    await _save_artifact(session, project, "requirements", json.dumps(requirements))


@enforce_state(from_=[ProjectStatus.DISCOVERY], to=ProjectStatus.PLANNING)
async def _plan(*, project: Project, session: AsyncSession):
    plan_obj = {
        "dag": {"nodes": [], "edges": []},
        "summary": "Auto-generated plan",
    }
    validate_schema(plan_obj, "plan")
    content = json.dumps(plan_obj)
    await _save_artifact(session, project, "plan", content)


@enforce_state(from_=[ProjectStatus.PLANNING], to=ProjectStatus.DESIGN)
async def _approve(*, project: Project, session: AsyncSession, gate: ProjectStatus):
    if gate != ProjectStatus.PLANNING:
        raise HTTPException(status_code=400, detail="Unsupported gate")


@enforce_state(from_=[ProjectStatus.DESIGN], to=ProjectStatus.BUILD)
async def _design(*, project: Project, session: AsyncSession):
    await _save_artifact(session, project, "openapi", json.dumps({"openapi": "3.0.0"}))
    await _save_artifact(session, project, "events", json.dumps({"events": []}))
    await _save_artifact(session, project, "adrs", "# Architecture Decision Records\n")


async def _build(*, project: Project, session: AsyncSession):
    for i in range(3):
        await manager.broadcast({"type": "job.started", "node": i})


@enforce_state(from_=[ProjectStatus.BUILD], to=ProjectStatus.TEST)
async def _test(*, project: Project, session: AsyncSession):
    report = {"passed": True}
    validate_schema(report, "test_report")
    await _save_artifact(session, project, "test_report", json.dumps(report))
    await manager.broadcast({"type": "qa.report", "status": "passed"})


@enforce_state(from_=[ProjectStatus.REVIEW], to=ProjectStatus.DEPLOY)
async def _deploy(*, project: Project, session: AsyncSession):
    await manager.broadcast({"type": "deploy.status", "status": "success"})
