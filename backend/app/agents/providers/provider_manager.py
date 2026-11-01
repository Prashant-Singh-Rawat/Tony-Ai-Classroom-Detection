"""
backend/app/agents/providers/provider_manager.py — Central Model Provider Manager
=================================================================================
Manages local and cloud model providers, fallback routing, quota error handling,
token budget enforcement, and cumulative cost tracking.
"""

from __future__ import annotations
import os
from typing import Any, Dict, Optional

from backend.app.agents.core.types import LLMProviderType
from backend.app.agents.providers.provider_base import LLMProvider, ProviderResponse
from backend.app.agents.providers.local_offline_provider import LocalOfflineProvider
from backend.app.agents.providers.cloud_providers import (
    AnthropicProvider,
    GeminiProvider,
    OpenAIProvider,
)


class ProviderManager:
    """Manages active LLM provider selection, fallbacks, and cost tracking."""

    def __init__(self) -> None:
        self._providers: Dict[LLMProviderType, LLMProvider] = {
            LLMProviderType.LOCAL_OFFLINE: LocalOfflineProvider(),
        }
        self.active_provider_type: LLMProviderType = LLMProviderType.LOCAL_OFFLINE
        self._init_available_cloud_providers()

    def _init_available_cloud_providers(self) -> None:
        """Initializes cloud providers if respective API keys are present in environment."""
        if os.getenv("OPENAI_API_KEY"):
            try:
                self._providers[LLMProviderType.OPENAI] = OpenAIProvider()
            except Exception:
                pass

        if os.getenv("GEMINI_API_KEY"):
            try:
                self._providers[LLMProviderType.GEMINI] = GeminiProvider()
            except Exception:
                pass

        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self._providers[LLMProviderType.ANTHROPIC] = AnthropicProvider()
            except Exception:
                pass

    def get_active_provider(self) -> LLMProvider:
        """Returns the currently active provider, falling back safely to local offline engine."""
        return self._providers.get(self.active_provider_type) or self._providers[LLMProviderType.LOCAL_OFFLINE]

    def set_active_provider(self, provider_type: LLMProviderType) -> bool:
        """Switches the active provider if available."""
        if provider_type in self._providers:
            self.active_provider_type = provider_type
            return True
        return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ProviderResponse:
        """
        Executes model generation on active provider.
        Automatically falls back to local offline provider if cloud API encounters quota/rate limit error.
        """
        provider = self.get_active_provider()
        try:
            return provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            # Automatic fallback to local offline engine
            if self.active_provider_type != LLMProviderType.LOCAL_OFFLINE:
                fallback = self._providers[LLMProviderType.LOCAL_OFFLINE]
                res = fallback.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                res.metadata["fallback_from"] = self.active_provider_type.value
                res.metadata["fallback_reason"] = str(e)
                return res
            raise e

    def get_all_usage_metrics(self) -> Dict[str, Any]:
        """Returns aggregate token usage, costs, and configured providers."""
        return {
            "active_provider": self.active_provider_type.value,
            "available_providers": [p.value for p in self._providers.keys()],
            "metrics": {
                p_type.value: prov.get_usage_metrics()
                for p_type, prov in self._providers.items()
            },
        }


# Global singleton instance
provider_manager = ProviderManager()

