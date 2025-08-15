import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .ws_manager import ws_broadcast


@dataclass
class TestResult:
    passed: bool
    coverage: Optional[float] = None
    summary: str = ""


class TestRunner:
    async def run(self, project_id: int) -> TestResult:  # pragma: no cover - default stub
        await asyncio.sleep(0)
        return TestResult(passed=True, coverage=80.0, summary="stub")


class TestService:
    def __init__(self, runner: Optional[TestRunner] = None, broadcaster=ws_broadcast) -> None:
        self.runner = runner or TestRunner()
        self.broadcaster = broadcaster

    async def run_tests(self, project_id: int) -> Dict[str, Any]:
        result = await self.runner.run(project_id)
        report: Dict[str, Any] = {
            "passed": bool(result.passed),
            "coverage": result.coverage,
            "summary": result.summary,
        }
        await self.broadcaster(
            {
                "type": "qa.report",
                "project_id": project_id,
                "payload": report,
            }
        )
        return report

