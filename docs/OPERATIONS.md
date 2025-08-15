# Operations

This document covers secrets, sandboxing, and backups for safe operation.

## Secrets

- Read from environment variables only; never log secrets.
- Optional provider keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.
- Optional basic auth: set `BASIC_AUTH_ENABLED=true`, `BASIC_AUTH_USER`, `BASIC_AUTH_PASS`.
- Logging scrubs sensitive fields (authorization, token, api_key, secret).

## Sandbox

- File system: `FSService` enforces project root; path traversal returns HTTP 403.
- Shell: `ShellSandbox` allows only a safe command allowlist (no network tools by default) and confines cwd to root.
- WebSockets: per-project throttle (~100 msgs/sec) to avoid floods.
- REST: `RateLimitMiddleware` (default 120 req/min/IP) and optional `BasicAuthMiddleware`.

## Backups

- Artifacts may be stored inline or via `uri` (external file). For files at `uri`, back up the `artifacts/` directory.
- Database backup (SQLModel): perform regular dumps; for SQLite, back up the `.db` file with the service stopped.
- Consider storing critical artifacts (plans, contracts, runbooks) in a VCS branch for redundancy.

