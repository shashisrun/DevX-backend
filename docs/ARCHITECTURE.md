# Architecture

This backend coordinates autonomous multi-agent SDLC with FastAPI + Celery. It persists artifacts and uses a state machine to control progression.

## Components

- API (`FastAPI`): REST endpoints + WebSocket for events.
- Agents: Planner, Designer, Implementer, Tester, Reviewer, Deployer, Critic.
- Services: DAG runner, FS, Diff, Git, Deploy, Test, Sandbox, WS manager.
- DB (`SQLModel`): Projects, Artifacts, Files.
- Task Queue (`Celery`): Long-running or parallelizable work.

## Sequence (happy path)

1. `/api/projects/{id}/init` → save `requirements` → Planner runs → `plan` artifact.
2. `/api/projects/{id}/plan` → advances to `PLANNING` (uses existing plan).
3. `/api/projects/{id}/design` → Designer runs → saves `openapi`, `events`, `adrs` → state `BUILD`.
4. Implementer/Reviewer/Critic run via `DevService` → branches, commits, PR artifact.
5. `/api/projects/{id}/test` → Tester runs → saves `test_report` → `REVIEW` on pass, `TEST_FAIL` on fail.
6. `/api/projects/{id}/deploy` → build image + manifests + runbook → `MONITOR` on success.

## Events (WebSocket)

Events follow `backend/contracts/events.schema.json`. Common types:
- `state.changed` — lifecycle status updated.
- `job.started|progress|completed|failed` — job orchestration.
- `qa.report` — test results summary.
- `deploy.status` — deploy stage updates.

