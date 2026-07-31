"""Abstract Base AI Provider implementation for HTTP-based LLM providers (Phase 10.2).

Provides reusable configuration management, API key lookup, HTTP client configuration,
and standard prompt message formatting.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import httpx

from brain.ai.exceptions import ProviderUnavailableError
from brain.ai.interfaces import AIProvider
from brain.ai.ai_models import AIRequest, AIResponse, Prompt, ProviderInfo
from brain.ai.provider_config import ProviderConfig


class BaseAIProvider(AIProvider, ABC):
    """Base class for all HTTP-based concrete LLM providers in Auralis."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._client: Optional[httpx.Client] = None

    def get_info(self) -> ProviderInfo:
        """Return provider metadata snapshot."""
        return ProviderInfo(
            provider_id=f"provider-{self.config.provider_name}",
            name=self.config.provider_name,
            version="1.0.0",
            is_available=self.is_available(),
            supported_features=[
                feat
                for feat, enabled in [
                    ("streaming", self.config.supports_streaming),
                    ("tools", self.config.supports_tools),
                    ("reasoning", self.config.supports_reasoning),
                    ("images", self.config.supports_images),
                ]
                if enabled
            ],
            max_context_window=128000,
            default_model_name=self.config.model_name,
            metadata={"base_url": self.config.base_url, "api_key_env": self.config.api_key_env},
        )

    def is_available(self) -> bool:
        """Check if provider is enabled and required API key environment variable is set."""
        if not self.config.enabled:
            return False

        api_key = os.getenv(self.config.api_key_env)
        return bool(api_key and api_key.strip())

    def get_api_key(self) -> str:
        """Retrieve configured API key from environment variable.

        Raises:
            ProviderUnavailableError: If API key is missing or empty.
        """
        api_key = os.getenv(self.config.api_key_env)
        if not api_key or not api_key.strip():
            raise ProviderUnavailableError(
                self.config.provider_name,
                reason=f"Environment variable '{self.config.api_key_env}' is not set or empty.",
            )
        return api_key.strip()

    def format_prompt_messages(self, prompt: Prompt) -> List[Dict[str, Any]]:
        """Format Prompt object into standard OpenAI-compatible messages array."""
        messages: List[Dict[str, Any]] = []

        if prompt.formatted_messages:
            for msg in prompt.formatted_messages:
                role_str = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
                # Map non-standard roles to system or user for standard LLM endpoints if needed
                if role_str in ("developer", "memory"):
                    role_str = "system"
                messages.append({"role": role_str, "content": msg.content})
        else:
            if prompt.system_prompt:
                messages.append({"role": "system", "content": prompt.system_prompt})
            if prompt.developer_prompt:
                messages.append({"role": "system", "content": prompt.developer_prompt})
            if prompt.memory_prompt:
                messages.append({"role": "system", "content": prompt.memory_prompt})
            if prompt.tool_prompt:
                messages.append({"role": "system", "content": prompt.tool_prompt})
            if prompt.user_prompt:
                messages.append({"role": "user", "content": prompt.user_prompt})

        return messages

    def _get_client(self) -> httpx.Client:
        """Get or create reusable httpx.Client session."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=self.config.timeout)
        return self._client

    def close(self) -> None:
        """Close underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            self._client.close()

    @abstractmethod
    def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate response from model endpoint."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform health diagnostic check."""
        pass
