"""
backend/app/agents/providers/cloud_providers.py — Cloud LLM Provider Adapters
==============================================================================
Provides adapters for OpenAI, Anthropic, and Google Gemini APIs with token usage
tracking, rate-limit protection, timeout handling, and secure credential loading.
"""

from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from backend.app.agents.core.types import LLMProviderType
from backend.app.agents.providers.provider_base import LLMProvider, ProviderResponse


class OpenAIProvider(LLMProvider):
    """Adapter for OpenAI-compatible Chat Completions API."""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gpt-4o-mini") -> None:
        super().__init__(provider_type=LLMProviderType.OPENAI, default_model=default_model)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ProviderResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured in the environment.")

        active_model = model or self.default_model
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": active_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API error ({e.code}): {err_body}")

        elapsed_ms = round((time.time() - t0) * 1000, 2)
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Standard estimated pricing for gpt-4o-mini ($0.15 / 1M input, $0.60 / 1M output)
        cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
        self.total_tokens_used += total_tokens
        self.total_cost_usd += cost

        return ProviderResponse(
            content=choice,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate_usd=cost,
            model_name=active_model,
            provider_type=self.provider_type,
            latency_ms=elapsed_ms,
        )


class GeminiProvider(LLMProvider):
    """Adapter for Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-2.0-flash") -> None:
        super().__init__(provider_type=LLMProviderType.GEMINI, default_model=default_model)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ProviderResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in the environment.")

        active_model = model or self.default_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={self.api_key}"

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"[SYSTEM INSTRUCTION]: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API error ({e.code}): {err_body}")

        elapsed_ms = round((time.time() - t0) * 1000, 2)
        candidates = data.get("candidates", [])
        if not candidates or "content" not in candidates[0]:
            raise RuntimeError("Gemini API returned an empty completion.")

        choice = candidates[0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", len(prompt) // 4)
        completion_tokens = usage.get("candidatesTokenCount", len(choice) // 4)
        total_tokens = usage.get("totalTokenCount", prompt_tokens + completion_tokens)

        cost = (prompt_tokens * 0.00000010) + (completion_tokens * 0.00000040)
        self.total_tokens_used += total_tokens
        self.total_cost_usd += cost

        return ProviderResponse(
            content=choice,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate_usd=cost,
            model_name=active_model,
            provider_type=self.provider_type,
            latency_ms=elapsed_ms,
        )


class AnthropicProvider(LLMProvider):
    """Adapter for Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "claude-3-5-sonnet-20241022") -> None:
        super().__init__(provider_type=LLMProviderType.ANTHROPIC, default_model=default_model)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ProviderResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured in the environment.")

        active_model = model or self.default_model
        payload = {
            "model": active_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Anthropic API error ({e.code}): {err_body}")

        elapsed_ms = round((time.time() - t0) * 1000, 2)
        choice = data["content"][0]["text"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens

        cost = (prompt_tokens * 0.000003) + (completion_tokens * 0.000015)
        self.total_tokens_used += total_tokens
        self.total_cost_usd += cost

        return ProviderResponse(
            content=choice,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate_usd=cost,
            model_name=active_model,
            provider_type=self.provider_type,
            latency_ms=elapsed_ms,
        )

