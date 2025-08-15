import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from ..models.artifact import Artifact
from ..models.project import Project
from ..services.ws_manager import ws_broadcast
from .git_service import GitService


@dataclass
class ReviewResult:
    approved: bool
    changes_requested: bool = False
    critique: Optional[str] = None


class DevService:
    """Implements implementer→reviewer→critic loop with patch application and WS events."""

    def __init__(self, git: Optional[GitService] = None, broadcaster=ws_broadcast) -> None:
        self.git = git or GitService()
        self.broadcaster = broadcaster

    async def _emit(self, project_id: int, type_: str, payload: Dict[str, Any]) -> None:
        await self.broadcaster({"type": type_, "project_id": project_id, "payload": payload})

    async def _persist_artifact(self, session: AsyncSession, project_id: int, kind: str, content: str) -> Artifact:
        art = Artifact(project_id=project_id, kind=kind, content=content)
        session.add(art)
        await session.commit()
        await session.refresh(art)
        return art

    def _count_changes(self, patch: str) -> Tuple[int, int]:
        files, tests = 0, 0
        for line in patch.splitlines():
            if line.startswith("+++ "):
                files += 1
                if "/tests/" in line or line.endswith("tests\n"):
                    tests += 1
        return files, tests

    async def implement(self, project: Project, node: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        branch = node.get("branch") or f"feature/{node.get('id', uuid4().hex[:8])}"
        await self._emit(project.id, "job.progress", {"job_id": job_id, "stage": "implement", "msg": f"create branch {branch}"})
        await self.git.create_branch(branch)
        patches: List[str] = node.get("patches") or []
        if not patches:
            # synthesize a trivial patch if none provided
            patches = [
                """--- /dev/null\n+++ README_AUTOGEN.md\n@@ -0,0 +1,2 @@\n+# Auto Feature\n+Generated content\n"""
            ]
        total_files, total_tests = 0, 0
        for p in patches:
            f, t = self._count_changes(p)
            total_files += max(1, f)  # conservative
            total_tests += t
            await self._emit(project.id, "job.progress", {"job_id": job_id, "stage": "implement", "msg": "apply patch"})
            await self.git.apply_patch(p)
        await self.git.commit_all(node.get("commit_message", "Implement feature"))
        await self._emit(project.id, "job.progress", {"job_id": job_id, "stage": "implement", "files_changed": total_files, "tests_updated": total_tests})
        return {"branch": branch, "files_changed": total_files, "tests_updated": total_tests}

    async def reviewer(self, project: Project, context: Dict[str, Any], critique_once: bool = False) -> ReviewResult:
        # Simple heuristic: if critique_once True and not yet iterated, request changes once.
        if critique_once and not context.get("_reviewed_once"):
            context["_reviewed_once"] = True
            return ReviewResult(approved=False, changes_requested=True, critique="Tighten tests and naming.")
        return ReviewResult(approved=True)

    async def critic(self, project: Project, context: Dict[str, Any], veto: bool = False) -> ReviewResult:
        if veto:
            return ReviewResult(approved=False, changes_requested=False, critique="Independent critic veto.")
        return ReviewResult(approved=True)

    async def run_feature_node(
        self,
        session: AsyncSession,
        project: Project,
        node: Dict[str, Any],
        *,
        request_changes_once: bool = True,
        critic_veto: bool = False,
    ) -> Dict[str, Any]:
        job_id = uuid4().hex
        await self._emit(project.id, "job.started", {"job_id": job_id, "stage": "dev"})
        try:
            impl = await self.implement(project, node, job_id)
            # reviewer loop
            review = await self.reviewer(project, impl, critique_once=request_changes_once)
            if review.changes_requested:
                # perform re-implementation using critique (could adjust patches)
                await self._emit(project.id, "job.progress", {"job_id": job_id, "stage": "review", "action": "changes_requested", "critique": review.critique})
                # re-apply same patches for simplicity; in real impl derive new patches from critique
                await self.implement(project, node, job_id)
                review = await self.reviewer(project, impl, critique_once=False)

            # independent critic
            crit = await self.critic(project, impl, veto=critic_veto)
            if not review.approved or not crit.approved:
                await self._emit(project.id, "job.failed", {"job_id": job_id, "reason": review.critique or "critic veto"})
                return {"status": "failed", "job_id": job_id}

            # create PR artifact
            pr_title = node.get("title", "Feature")
            pr_body = node.get("summary", "")
            pr_url = await self.git.create_pr(pr_title, pr_body)
            summary_md = f"# PR: {pr_title}\n\nBranch: `{impl['branch']}`\n\nURL: {pr_url}\n\nSummary:\n\n{pr_body}\n"
            await self._persist_artifact(session, project.id, "pr", summary_md)
            await self._emit(project.id, "job.completed", {"job_id": job_id, "branch": impl["branch"], "pr_url": pr_url})
            return {"status": "done", "job_id": job_id, "branch": impl["branch"], "pr_url": pr_url}
        except Exception as e:  # pragma: no cover - defensive
            await self._emit(project.id, "job.failed", {"job_id": job_id, "error": str(e)})
            return {"status": "failed", "job_id": job_id, "error": str(e)}

