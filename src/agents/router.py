import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

@dataclass
class ModelSpec:
    provider: str
    model: str
    params: Dict[str, Any] = field(default_factory=dict)
    budgets: Dict[str, Any] = field(default_factory=dict)
    cost_per_token: float = 0.0


class ModelRouter:
    """Route LLM requests across providers with fallback and budgeting."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).with_name("config") / "models.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        self.policies: Dict[str, Dict[str, List[ModelSpec] | ModelSpec]] = {}
        for role, cfg in raw.items():
            primary = ModelSpec(**cfg["primary"])
            fallbacks = [ModelSpec(**fb) for fb in cfg.get("fallbacks", [])]
            self.policies[role] = {"primary": primary, "fallbacks": fallbacks}

    async def chat(self, role: str, messages: List[Dict[str, str]], job: Optional[Any] = None) -> str:
        if role not in self.policies:
            raise KeyError(f"unknown role {role}")
        policy = self.policies[role]
        models: List[ModelSpec] = [policy["primary"]] + policy.get("fallbacks", [])
        last_error: Optional[Exception] = None
        for spec in models:
            try:
                start = time.perf_counter()
                data = await self._invoke(spec.provider, spec.model, messages, spec.params)
                latency = time.perf_counter() - start
                tokens = data.get("usage", {}).get("total_tokens", 0)
                max_tokens = spec.budgets.get("max_tokens")
                if max_tokens is not None and tokens > max_tokens:
                    raise ValueError("token budget exceeded")
                max_latency = spec.budgets.get("max_latency")
                if max_latency is not None and latency > max_latency:
                    raise TimeoutError("latency budget exceeded")
                cost = tokens * spec.cost_per_token
                record = {
                    "provider": spec.provider,
                    "model": spec.model,
                    "tokens": tokens,
                    "latency": latency,
                    "cost": cost,
                }
                if job is not None and hasattr(job, "outputs"):
                    job.outputs.append(record)
                return data["choices"][0]["message"]["content"]
            except Exception as e:  # pragma: no cover - fallback path tested separately
                last_error = e
                continue
        raise last_error or RuntimeError("all providers failed")

    async def _invoke(
        self, provider: str, model: str, messages: List[Dict[str, str]], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call out to a provider via LiteLLM."""
        import litellm

        kwargs = {"model": model, "messages": messages, **params}
        env_key = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        if api_key:
            kwargs["api_key"] = api_key
        return await litellm.acompletion(**kwargs)


__all__ = ["ModelRouter"]
