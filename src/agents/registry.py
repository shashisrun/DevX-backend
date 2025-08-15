from typing import Awaitable, Callable, Dict

from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.artifact import Artifact
from .contracts import (
    PlannerInput,
    PlannerOutput,
    DesignerInput,
    DesignerOutput,
    ImplementerInput,
    ImplementerOutput,
    TesterInput,
    TesterOutput,
    ReviewerInput,
    ReviewerOutput,
    DeployerInput,
    DeployerOutput,
    CriticInput,
    CriticOutput,
)

AgentFunc = Callable[[AsyncSession, int, BaseModel], Awaitable[BaseModel]]


async def _persist(session: AsyncSession, project_id: int, kind: str, content: str) -> Artifact:
    artifact = Artifact(project_id=project_id, kind=kind, content=content)
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)
    return artifact


async def planner(session: AsyncSession, project_id: int, inp: PlannerInput) -> PlannerOutput:
    output = PlannerOutput(dag={"nodes": [], "edges": []}, acceptance=[])
    await _persist(session, project_id, "plan", output.model_dump_json())
    return output


async def designer(session: AsyncSession, project_id: int, inp: DesignerInput) -> DesignerOutput:
    output = DesignerOutput(openapi={}, adrs=[])
    await _persist(session, project_id, "design", output.model_dump_json())
    return output


async def implementer(session: AsyncSession, project_id: int, inp: ImplementerInput) -> ImplementerOutput:
    output = ImplementerOutput(patches=[])
    await _persist(session, project_id, "patches", output.model_dump_json())
    return output


async def tester(session: AsyncSession, project_id: int, inp: TesterInput) -> TesterOutput:
    output = TesterOutput(report="")
    await _persist(session, project_id, "test-report", output.model_dump_json())
    return output


async def reviewer(session: AsyncSession, project_id: int, inp: ReviewerInput) -> ReviewerOutput:
    output = ReviewerOutput(approved=True, comments=[])
    await _persist(session, project_id, "review", output.model_dump_json())
    return output


async def deployer(session: AsyncSession, project_id: int, inp: DeployerInput) -> DeployerOutput:
    output = DeployerOutput(image_refs=[], runbook="")
    await _persist(session, project_id, "deployment", output.model_dump_json())
    return output


async def critic(session: AsyncSession, project_id: int, inp: CriticInput) -> CriticOutput:
    output = CriticOutput(findings=[], suggestions=[])
    await _persist(session, project_id, "critique", output.model_dump_json())
    return output


agent_registry: Dict[str, Callable[..., Awaitable[BaseModel]]] = {
    "planner": planner,
    "designer": designer,
    "implementer": implementer,
    "tester": tester,
    "reviewer": reviewer,
    "deployer": deployer,
    "critic": critic,
}
