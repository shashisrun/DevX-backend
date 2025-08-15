# API

Base URL: `http://localhost:8000`

## REST

- `GET /health` → `{status: "ok"}`
- `GET /api/projects/` → list projects
- `POST /api/projects/` `{name}` → create project
- `POST /api/projects/{id}/init` `{requirements}` → save requirements, fire planner
- `POST /api/projects/{id}/plan` → advance to PLANNING (reuses plan)
- `POST /api/projects/{id}/approve?gate=PLANNING` → PLANNING→DESIGN (when approval gate enabled)
- `POST /api/projects/{id}/design` → produce contracts, advance to BUILD
- `POST /api/projects/{id}/test` → run tests, save `test_report`; TEST→REVIEW or TEST→TEST_FAIL
- `POST /api/projects/{id}/deploy` → build, write runbook; DEPLOY→MONITOR on success
- `GET /api/projects/{id}/artifacts?kind=...` → list artifacts (content or `uri` backed)
- `GET /api/projects/{id}/contracts` → `{ openapi, events }`

### Examples

Create a project:
```
curl -s -X POST localhost:8000/api/projects/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo"}'
```

Initialize requirements:
```
curl -s -X POST localhost:8000/api/projects/1/init \
  -H 'Content-Type: application/json' \
  -d '{"features":["search","auth"]}'
```

## WebSocket

- `GET /ws/{project_id}`
- Sends JSON events. Schema: `backend/contracts/events.schema.json`.

Example:
```
{
  "type": "job.progress",
  "project_id": 1,
  "payload": { "job_id": "abc", "current": 2, "total": 5 },
  "ts": "2024-08-15T18:30:00Z",
  "trace_id": "..."
}
```

## OpenAPI Schema

- Live schema: `GET /openapi.json`
- Swagger UI: `GET /docs`
- Snapshot: see `docs/openapi.json` (may be slightly stale).
