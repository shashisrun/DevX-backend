# Agents

Agents implement role-specific logic with typed contracts (Pydantic models in `src/agents/contracts.py`). Implementations live in `src/agents/registry.py` and services.

## Roles

- Planner: inputs requirements → outputs Plan DAG and acceptance criteria.
- Designer: inputs plan → outputs OpenAPI, ADRs, and design docs.
- Implementer: inputs design/plan node → applies patches, commits to a branch.
- Reviewer: lints/security/perf; can request changes (rework once).
- Critic: independent check; reduces bias; can veto.
- Tester: runs tests, may generate minimal failing tests; emits QA report.
- Deployer: builds image, generates manifests, runs smoke tests; writes runbook.

## Contracts

See `src/agents/contracts.py` for input/output models and `tests/test_agent_contracts.py` for validation.

## Provider Routing

`src/agents/router.py` routes to the best provider per role using LiteLLM. Configure models and budgets in `src/agents/config/models.yaml`. Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` as needed.

