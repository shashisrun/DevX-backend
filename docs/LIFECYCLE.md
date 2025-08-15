# Lifecycle

Project states and legal transitions are enforced by `src/utils/state_machine.py`.

## States

`NEW → DISCOVERY → PLANNING → DESIGN → BUILD → TEST → REVIEW → DEPLOY → MONITOR → DONE`

Failure/loopback states:
- `TEST_FAIL → ROLLBACK → BUILD`

## Gates

- Optional approval gate before design: set `REQUIRE_APPROVAL_PLANNING=true`.
- Approve via: `POST /api/projects/{id}/approve?gate=PLANNING`.

## Autonomous flow

- `/init` saves `requirements`, triggers Planner, stays in `DISCOVERY`.
- `/plan` advances to `PLANNING` (reuses plan if present).
- `/design` generates contracts and advances to `BUILD` (blocked if approval gate on and still `PLANNING`).
- `/test` advances `BUILD→TEST` and then to `REVIEW` on pass, `TEST_FAIL` on fail.
- `/deploy` advances `REVIEW→DEPLOY` and to `MONITOR` when smoke tests pass.

