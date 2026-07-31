"""Groq AI Provider implementation for Auralis (Phase 10.2).

Implements AIProvider interface targeting Groq Cloud API (/chat/completions & /models).
Supports text completion, tool calling, sampling controls, and health diagnostics.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import httpx

from brain.ai.exceptions import AIException, ProviderUnavailableError
from brain.ai.ai_models import (
    AIRequest,
    AIResponse,
    FinishReason,
    ToolCall,
    ToolCategory,
)
from brain.ai.provider_config import ProviderConfig, get_groq_default_config
from brain.ai.providers.base_provider import BaseAIProvider


class GroqProvider(BaseAIProvider):
    """Concrete Groq LLM Provider implementation using OpenAI-compatible API format."""

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        cfg = config or get_groq_default_config()
        super().__init__(cfg)

    def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate response payload from Groq Cloud API.

        Args:
            request: AIRequest payload containing prompt, parameters, and tools.

        Returns:
            AIResponse object with generated text, tool calls, and usage stats.

        Raises:
            ProviderUnavailableError: If API call fails or service is unreachable.
            AIException: If API returns malformed response data.
        """
        api_key = self.get_api_key()
        base_url = self.config.base_url or "https://api.groq.com/openai/v1"
        endpoint = f"{base_url.rstrip('/')}/chat/completions"

        messages = self.format_prompt_messages(request.prompt)

        payload: Dict[str, Any] = {
            "model": request.parameters.get("model", self.config.model_name),
            "messages": messages,
            "temperature": request.parameters.get("temperature", self.config.temperature),
            "top_p": request.parameters.get("top_p", self.config.top_p),
        }

        max_tokens = request.parameters.get("max_tokens", self.config.max_tokens)
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if request.tools and self.config.supports_tools:
            payload["tools"] = request.tools

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        client = self._get_client()

        try:
            res = client.post(endpoint, json=payload, headers=headers)
            if res.status_code != 200:
                raise ProviderUnavailableError(
                    self.config.provider_name,
                    reason=f"HTTP {res.status_code}: {res.text[:200]}",
                )

            data = res.json()
            return self._parse_groq_response(data, request.request_id)
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                self.config.provider_name,
                reason=f"HTTP request failed: {exc}",
            ) from exc
        except Exception as exc:
            if isinstance(exc, (ProviderUnavailableError, AIException)):
                raise
            raise AIException(f"Failed to process Groq completion: {exc}") from exc

    def health_check(self) -> Dict[str, Any]:
        """Perform diagnostic health check against Groq API endpoint."""
        if not self.is_available():
            return {
                "status": "unavailable",
                "healthy": False,
                "reason": "API key missing or provider disabled",
                "provider": self.config.provider_name,
            }

        api_key = self.get_api_key()
        base_url = self.config.base_url or "https://api.groq.com/openai/v1"
        endpoint = f"{base_url.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {api_key}"}

        start_time = time.perf_counter()
        client = self._get_client()

        try:
            res = client.get(endpoint, headers=headers)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if res.status_code == 200:
                return {
                    "status": "ok",
                    "healthy": True,
                    "latency_ms": elapsed_ms,
                    "model": self.config.model_name,
                    "provider": self.config.provider_name,
                }
            else:
                return {
                    "status": "error",
                    "healthy": False,
                    "http_status": res.status_code,
                    "error": res.text[:200],
                    "provider": self.config.provider_name,
                }
        except Exception as exc:
            return {
                "status": "error",
                "healthy": False,
                "error": str(exc),
                "provider": self.config.provider_name,
            }

    def _parse_groq_response(self, data: Dict[str, Any], request_id: str) -> AIResponse:
        """Parse raw Groq API JSON response dictionary into AIResponse model."""
        response_id = data.get("id", f"res-groq-{uuid.uuid4().hex[:8]}")
        choices = data.get("choices", [])
        if not choices:
            raise AIException("Groq API returned empty choices array.")

        first_choice = choices[0]
        msg = first_choice.get("message", {})
        text_content = msg.get("content") or ""

        finish_reason_raw = first_choice.get("finish_reason", "stop")
        finish_reason = self._map_finish_reason(finish_reason_raw)

        # Parse tool calls if present
        parsed_tool_calls: List[ToolCall] = []
        raw_tool_calls = msg.get("tool_calls", [])
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            call_id = tc.get("id", f"call-{uuid.uuid4().hex[:8]}")
            tool_name = func.get("name", "unknown")
            args_raw = func.get("arguments", {})

            # Parse string arguments if returned as JSON string
            if isinstance(args_raw, str):
                import json
                try:
                    args_dict = json.loads(args_raw)
                except Exception:
                    args_dict = {"raw": args_raw}
            elif isinstance(args_raw, dict):
                args_dict = args_raw
            else:
                args_dict = {}

            parsed_tool_calls.append(
                ToolCall(
                    call_id=call_id,
                    tool_name=tool_name,
                    arguments=args_dict,
                    category=ToolCategory.FILESYSTEM,
                )
            )

        usage = data.get("usage", {})
        usage_stats = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

        return AIResponse(
            response_id=response_id,
            request_id=request_id,
            text=text_content,
            tool_calls=parsed_tool_calls,
            finish_reason=finish_reason,
            usage_stats=usage_stats,
            raw_response=data,
            provider_name=self.config.provider_name,
        )

    def _map_finish_reason(self, reason_str: str) -> FinishReason:
        """Map raw API finish_reason string to FinishReason enum."""
        mapping = {
            "stop": FinishReason.STOP,
            "tool_calls": FinishReason.TOOL_CALLS,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
        }
        return mapping.get(reason_str.lower(), FinishReason.STOP)
