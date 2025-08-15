import asyncio
from dataclasses import dataclass
from graphlib import TopologicalSorter
from typing import Dict, List

from celery import group

from .task_queue import celery_app
from .ws_manager import ws_broadcast
from ..models.enums import JobState


@dataclass
class Job:
    id: int
    project_id: int
    state: JobState = JobState.PENDING
    progress: int = 0
    total: int = 0


class DAGRunner:
    """Execute a plan DAG using Celery tasks."""

    TASK_MAP = {
        "index_repo": "index_repo",
        "implement_endpoints": "implement_endpoints",
        "write_tests": "write_tests",
        "configure_ci": "configure_ci",
    }

    def __init__(self, app=celery_app, broadcaster=ws_broadcast):
        self.app = app
        self.broadcaster = broadcaster

    def _emit(self, event: dict) -> None:
        asyncio.run(self.broadcaster(event))

    def run(self, plan: Dict, project_id: int, job_id: int) -> JobState:
        dag = plan["dag"]
        node_map = {n["id"]: n for n in dag["nodes"]}
        graph: Dict[str, set] = {node_id: set() for node_id in node_map}
        for src, dst in dag.get("edges", []):
            graph[dst].add(src)

        ts = TopologicalSorter(graph)
        ts.prepare()

        job = Job(job_id, project_id, state=JobState.RUNNING, total=len(node_map))
        self._emit({"type": "job.started", "project_id": project_id, "payload": {"job_id": job_id}})

        try:
            while ts.is_active():
                ready = list(ts.get_ready())
                sigs: List = []
                for node_id in ready:
                    node = node_map[node_id]
                    task_name = self.TASK_MAP.get(node["type"])
                    if task_name is None:
                        raise ValueError(f"unknown node type {node['type']}")
                    sigs.append(self.app.signature(task_name, args=(job_id, project_id, node.get("params", {}))))
                result = group(sigs).apply_async()
                result.get()
                job.progress += len(ready)
                self._emit({
                    "type": "job.progress",
                    "project_id": project_id,
                    "payload": {"job_id": job_id, "current": job.progress, "total": job.total},
                })
                ts.done(*ready)
            job.state = JobState.DONE
            self._emit({"type": "job.completed", "project_id": project_id, "payload": {"job_id": job_id}})
        except Exception as e:  # pragma: no cover - error path
            job.state = JobState.FAILED
            self._emit({
                "type": "job.failed",
                "project_id": project_id,
                "payload": {"job_id": job_id, "error": str(e)},
            })
            raise
        return job.state
