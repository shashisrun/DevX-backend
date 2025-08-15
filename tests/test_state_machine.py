import pytest
from fastapi import HTTPException

from src.models.project import Project
from src.models.enums import ProjectStatus
from src.db import async_session
from src.utils.state_machine import advance_state


@pytest.mark.asyncio
async def test_state_machine_transitions():
    async with async_session() as session:
        project = Project(name="demo")
        session.add(project)
        await session.commit()
        await session.refresh(project)
        assert project.status == ProjectStatus.NEW
        await advance_state(session, project, ProjectStatus.DISCOVERY)
        assert project.status == ProjectStatus.DISCOVERY
        with pytest.raises(HTTPException):
            await advance_state(session, project, ProjectStatus.NEW)
