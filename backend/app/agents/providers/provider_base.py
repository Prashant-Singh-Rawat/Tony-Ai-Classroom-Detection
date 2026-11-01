"""
backend/app/agents/providers/provider_base.py — Abstract LLM Provider Interface
================================================================================
Provides standard generation interface, token tracking, latency recording,
and quota error protection across local and cloud language model backends.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.app.agents.core.types import LLMProviderType


@dataclass
class ProviderResponse:
    """Standardized response payload from any model provider."""

    content: str
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_estimate_usd: float = 0.0
    model_name: str = "default"
    provider_type: LLMProviderType = LLMProviderType.LOCAL_OFFLINE
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract interface for all model providers."""

    def __init__(self, provider_type: LLMProviderType, default_model: str) -> None:
        self.provider_type = provider_type
        self.default_model = default_model
        self.total_tokens_used: int = 0
        self.total_cost_usd: float = 0.0

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ProviderResponse:
        """Generates a text completion or structured response."""
        raise NotImplementedError

    def get_usage_metrics(self) -> Dict[str, Any]:
        """Returns cumulative token consumption and estimated costs."""
        return {
            "provider_type": self.provider_type.value,
            "default_model": self.default_model,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 5),
        }

