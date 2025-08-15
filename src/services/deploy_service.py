import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any

from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.artifact import Artifact
from ..models.project import Project
from .ws_manager import ws_broadcast


@dataclass
class DeployResult:
    ok: bool
    image_ref: str
    manifests_kind: Optional[str] = None


class DeployRunner:
    async def build_image(self, project: Project) -> str:  # pragma: no cover - default stub
        await asyncio.sleep(0)
        return f"{project.name.lower()}:latest"

    async def generate_manifests(self, project: Project, kind: str = "compose") -> str:  # pragma: no cover
        if kind == "compose":
            return (
                "version: '3'\nservices:\n  app:\n    image: ${IMAGE}\n    ports:\n      - '8000:8000'\n"
            )
        return (
            "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\nspec:\n  replicas: 1\n  template:\n    spec:\n      containers:\n      - name: app\n        image: ${IMAGE}\n"
        )

    async def run_smoke(self, image_ref: str) -> bool:  # pragma: no cover - default stub
        await asyncio.sleep(0)
        return True


class DeployService:
    def __init__(self, runner: Optional[DeployRunner] = None, broadcaster=ws_broadcast) -> None:
        self.runner = runner or DeployRunner()
        self.broadcaster = broadcaster

    async def _emit(self, project_id: int, payload: Dict[str, Any]) -> None:
        await self.broadcaster({"type": "deploy.status", "project_id": project_id, "payload": payload})

    async def _artifact(self, session: AsyncSession, project_id: int, kind: str, content: str) -> Artifact:
        art = Artifact(project_id=project_id, kind=kind, content=content)
        session.add(art)
        await session.commit()
        await session.refresh(art)
        return art

    async def deploy(self, session: AsyncSession, project: Project, *, manifests_kind: str = "compose") -> DeployResult:
        await self._emit(project.id, {"stage": "start"})
        image_ref = await self.runner.build_image(project)
        await self._emit(project.id, {"stage": "built", "image": image_ref})
        manifests = await self.runner.generate_manifests(project, manifests_kind)
        await self._artifact(session, project.id, "manifests", manifests)
        ok = await self.runner.run_smoke(image_ref)
        if ok:
            await self._emit(project.id, {"stage": "smoke_pass"})
        else:
            await self._emit(project.id, {"stage": "smoke_fail"})
        runbook = (
            f"# Runbook for {project.name}\n\n"
            f"- Image: `{image_ref}`\n"
            f"- Manifests: `{manifests_kind}`\n\n"
            "## Local run\n\n"
            "docker run -p 8000:8000 ${IMAGE}\n\n"
            "## Smoke test\n\n"
            "curl -f http://localhost:8000/health\n"
        )
        await self._artifact(session, project.id, "runbook", runbook)
        return DeployResult(ok=ok, image_ref=image_ref, manifests_kind=manifests_kind)

