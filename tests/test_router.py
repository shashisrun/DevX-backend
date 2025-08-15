import asyncio
import pytest

from src.agents.router import ModelRouter
from src.services.dag_runner import Job


def test_fallback_on_error(monkeypatch):
    router = ModelRouter()

    async def fake_invoke(self, provider, model, messages, params):
        if provider == "openai":
            raise RuntimeError("boom")
        return {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"total_tokens": 5},
        }

    monkeypatch.setattr(ModelRouter, "_invoke", fake_invoke, raising=False)
    job = Job(1, 1)
    result = asyncio.run(router.chat("planner", [{"role": "user", "content": "hi"}], job))
    assert result == "ok"
    assert job.outputs[0]["provider"] == "anthropic"
    assert job.outputs[0]["tokens"] == 5
    assert job.outputs[0]["cost"] > 0


def test_fallback_on_budget(monkeypatch):
    router = ModelRouter()

    async def fake_invoke(self, provider, model, messages, params):
        if provider == "openai":
            return {
                "choices": [{"message": {"content": "too many"}}],
                "usage": {"total_tokens": 2000},
            }
        return {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setattr(ModelRouter, "_invoke", fake_invoke, raising=False)
    job = Job(2, 1)
    result = asyncio.run(router.chat("planner", [{"role": "user", "content": "hi"}], job))
    assert result == "ok"
    assert job.outputs[0]["provider"] == "anthropic"
    assert job.outputs[0]["tokens"] == 10
    assert job.outputs[0]["cost"] > 0
