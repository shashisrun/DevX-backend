import asyncio

from src.services.dag_runner import DAGRunner
from src.services.task_queue import celery_app


def test_dag_runner_order_and_events():
    celery_app.conf.task_always_eager = True
    events = []

    async def fake_broadcast(event):
        events.append(event)

    runner = DAGRunner(app=celery_app, broadcaster=fake_broadcast)
    plan = {
        "dag": {
            "nodes": [
                {"id": "n1", "type": "index_repo", "params": {}},
                {"id": "n2", "type": "write_tests", "params": {}},
            ],
            "edges": [["n1", "n2"]],
        },
        "summary": "test",
    }

    state = runner.run(plan, project_id=1, job_id=1)
    assert state.name.lower() == "done"

    types = [e["type"] for e in events]
    assert types == [
        "job.started",
        "job.progress",
        "job.progress",
        "job.completed",
    ]
    assert events[1]["payload"]["current"] == 1
    assert events[2]["payload"]["current"] == 2
