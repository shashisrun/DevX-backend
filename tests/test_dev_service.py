import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from src.main import app
from src.db import async_session
from src.models.artifact import Artifact
from src.models.project import Project
from src.services.dev_service import DevService
from src.services.git_service import GitService, GitResult


class FakeGit(GitService):
    def __init__(self):
        super().__init__(workdir=".")
        self.calls = []

    async def create_branch(self, name: str) -> GitResult:
        self.calls.append(("create_branch", name))
        return GitResult(ok=True)

    async def apply_patch(self, patch: str) -> GitResult:
        self.calls.append(("apply_patch", patch))
        return GitResult(ok=True)

    async def commit_all(self, message: str) -> GitResult:
        self.calls.append(("commit_all", message))
        return GitResult(ok=True)

    async def create_pr(self, title: str, body: str) -> str:
        self.calls.append(("create_pr", title, body))
        return "https://example.local/pr/123"


@pytest.mark.asyncio
async def test_feature_flow_with_rework_and_pr_artifact():
    # create project
    async with async_session() as session:
        project = Project(name="feat")
        session.add(project)
        await session.commit()
        await session.refresh(project)

    fake_git = FakeGit()
    svc = DevService(git=fake_git)

    # a simple node with one patch
    patch = """--- a/README.md\n+++ b/README.md\n@@ -1,1 +1,2 @@\n-# Title\n+# Title\n+New line\n"""
    node = {"id": "n1", "title": "Add line", "summary": "Add a line to README", "patches": [patch]}

    with TestClient(app) as client:
        # subscribe to WS
        with client.websocket_connect(f"/ws/{project.id}") as ws:
            async with async_session() as session:
                result = client.portal.call(
                    svc.run_feature_node,
                    session,
                    project,
                    node,
                    request_changes_once=True,
                    critic_veto=False,
                )
                assert result["status"] == "done"
            # We expect at least started, some progress, completed
            msgs = []
            for _ in range(5):
                try:
                    msgs.append(ws.receive_json())
                except Exception:  # no more messages
                    break
            types = [m["type"] for m in msgs]
            assert "job.started" in types
            assert any(t == "job.progress" for t in types)
            assert "job.completed" in types

    # verify PR artifact saved
    async with async_session() as session:
        arts = (await session.execute(select(Artifact).where(Artifact.project_id == project.id).where(Artifact.kind == "pr"))).scalars().all()
        assert len(arts) == 1
        assert "PR:" in arts[0].content
        assert "Branch:" in arts[0].content

    # ensure rework loop occurred (commit called at least twice)
    calls = [c[0] for c in fake_git.calls]
    assert calls.count("commit_all") >= 2


@pytest.mark.asyncio
async def test_critic_veto_marks_failed():
    async with async_session() as session:
        project = Project(name="feat2")
        session.add(project)
        await session.commit()
        await session.refresh(project)

    fake_git = FakeGit()
    svc = DevService(git=fake_git)
    node = {"id": "n2", "title": "Change", "summary": "Minor"}

    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/{project.id}") as ws:
            async with async_session() as session:
                result = client.portal.call(
                    svc.run_feature_node,
                    session,
                    project,
                    node,
                    request_changes_once=False,
                    critic_veto=True,
                )
                assert result["status"] == "failed"
            # consume messages and ensure job.failed present
            seen_failed = False
            for _ in range(5):
                try:
                    evt = ws.receive_json()
                except Exception:
                    break
                if evt["type"] == "job.failed":
                    seen_failed = True
            assert seen_failed
