import asyncio
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from fastapi import HTTPException


@dataclass
class ExecResult:
    code: int
    stdout: str
    stderr: str


class ShellSandbox:
    """Constrained shell execution with allowlist and working dir boundary.

    - Only commands in allowlist may run.
    - Working directory is restricted to `root` and below.
    - Network is implicitly disallowed by virtue of command allowlist (i.e., no curl/wget).
    """

    def __init__(self, root: Optional[str | Path] = None, allowlist: Optional[Iterable[str]] = None) -> None:
        self.root = Path(root or Path.cwd()).resolve()
        self.allowlist = set(allowlist or {"echo", "ls", "cat", "pytest"})

    def _enforce_wd(self, cwd: Optional[str | Path]) -> Path:
        cwd_path = Path(cwd or self.root).resolve()
        try:
            cwd_path.relative_to(self.root)
        except ValueError as exc:
            raise HTTPException(status_code=403, detail="Working directory escapes sandbox root") from exc
        return cwd_path

    def _enforce_cmd(self, argv: List[str]) -> None:
        if not argv:
            raise HTTPException(status_code=400, detail="No command provided")
        cmd = Path(argv[0]).name
        if cmd not in self.allowlist:
            raise HTTPException(status_code=403, detail=f"Command '{cmd}' not allowed")

    async def run(self, argv: List[str], *, cwd: Optional[str | Path] = None, input: Optional[str] = None, timeout: Optional[float] = None) -> ExecResult:
        self._enforce_cmd(argv)
        run_cwd = self._enforce_wd(cwd)
        loop = asyncio.get_event_loop()

        def _exec() -> ExecResult:
            proc = subprocess.run(
                argv,
                cwd=str(run_cwd),
                input=input,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            return ExecResult(code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)

        return await loop.run_in_executor(None, _exec)

