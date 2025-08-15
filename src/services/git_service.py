import asyncio
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""


class GitService:
    """Minimal git wrapper used by implementer/reviewer flow.

    Methods are async and safe to monkeypatch in tests.
    """

    def __init__(self, workdir: Optional[str] = None) -> None:
        self.workdir = workdir or "."

    async def _run(self, *args: str) -> GitResult:
        loop = asyncio.get_event_loop()

        def _invoke() -> GitResult:
            try:
                proc = subprocess.run(
                    ["git", *args],
                    cwd=self.workdir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return GitResult(ok=proc.returncode == 0, stdout=proc.stdout, stderr=proc.stderr)
            except Exception as e:  # pragma: no cover - defensive
                return GitResult(ok=False, stderr=str(e))

        return await loop.run_in_executor(None, _invoke)

    async def create_branch(self, name: str) -> GitResult:
        # ensure repo exists and create/checkout branch
        res = await self._run("checkout", "-b", name)
        return res

    async def apply_patch(self, patch: str) -> GitResult:
        # apply a unified diff
        loop = asyncio.get_event_loop()

        def _apply() -> GitResult:
            try:
                proc = subprocess.run(
                    ["git", "apply", "-p0", "-"],
                    cwd=self.workdir,
                    input=patch,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                return GitResult(ok=proc.returncode == 0, stdout=proc.stdout, stderr=proc.stderr)
            except Exception as e:  # pragma: no cover - defensive
                return GitResult(ok=False, stderr=str(e))

        return await loop.run_in_executor(None, _apply)

    async def commit_all(self, message: str) -> GitResult:
        add = await self._run("add", "-A")
        if not add.ok:
            return add
        return await self._run("commit", "-m", message)

    async def create_pr(self, title: str, body: str) -> str:
        # Placeholder: In real impl integrate with hosting provider (GH/GitLab)
        # Return a synthetic URL; tests can monkeypatch this.
        return f"https://example.local/pr?title={title.replace(' ', '+')}"

