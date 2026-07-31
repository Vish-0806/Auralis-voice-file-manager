"""Unit tests for Phase 10.2: LLM Provider Framework.

Validates:
- ProviderConfig creation & environment variable loading
- GroqProvider initialization, get_info(), and is_available()
- GroqProvider.generate_response() text completion & tool calling with mocked HTTP
- GroqProvider.health_check() with mocked HTTP endpoints
- ProviderManager priority ordering, default provider selection, and automatic failover
- Zero real API calls (100% mocked HTTP layer)
"""

import os
import json
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
import httpx

from brain.ai import (
    AIRequest,
    AIResponse,
    FinishReason,
    GroqProvider,
    Prompt,
    PromptMessage,
    PromptRole,
    ProviderConfig,
    ProviderManager,
    ProviderUnavailableError,
    ToolCall,
    ToolCategory,
    get_groq_default_config,
    load_provider_config_from_env,
)


# ---------------------------------------------------------------------------
# Tests: ProviderConfig & Environment Loading
# ---------------------------------------------------------------------------


def test_provider_config_instantiation():
    """Test manual ProviderConfig instantiation and default field values."""
    config = ProviderConfig(
        provider_name="test_llm",
        model_name="test-model-v1",
        api_key_env="TEST_LLM_KEY",
        base_url="https://api.test.com/v1",
    )

    assert config.provider_name == "test_llm"
    assert config.model_name == "test-model-v1"
    assert config.api_key_env == "TEST_LLM_KEY"
    assert config.base_url == "https://api.test.com/v1"
    assert config.temperature == 0.7
    assert config.top_p == 1.0
    assert config.enabled is True


def test_load_provider_config_from_env(monkeypatch):
    """Test loading ProviderConfig dynamically from environment variables."""
    monkeypatch.setenv("CUSTOM_MODEL", "custom-model-99")
    monkeypatch.setenv("CUSTOM_BASE_URL", "https://custom.api/v1")
    monkeypatch.setenv("CUSTOM_TEMPERATURE", "0.2")

    cfg = load_provider_config_from_env(
        provider_name="custom",
        default_model="fallback-model",
        default_api_key_env="CUSTOM_KEY",
        prefix="CUSTOM_",
    )

    assert cfg.provider_name == "custom"
    assert cfg.model_name == "custom-model-99"
    assert cfg.base_url == "https://custom.api/v1"
    assert cfg.temperature == 0.2
    assert cfg.api_key_env == "CUSTOM_KEY"


def test_get_groq_default_config():
    """Test get_groq_default_config helper defaults."""
    cfg = get_groq_default_config()
    assert cfg.provider_name == "groq"
    assert cfg.model_name == "llama-3.3-70b-versatile"
    assert cfg.api_key_env == "GROQ_API_KEY"
    assert cfg.base_url == "https://api.groq.com/openai/v1"


# ---------------------------------------------------------------------------
# Tests: GroqProvider Basics & Availability
# ---------------------------------------------------------------------------


def test_groq_provider_availability(monkeypatch):
    """Test GroqProvider is_available checks environment variable."""
    provider = GroqProvider()

    # Key not set -> False
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert provider.is_available() is False

    # Key set -> True
    monkeypatch.setenv("GROQ_API_KEY", "gsk_dummy_key_12345")
    assert provider.is_available() is True

    # Info metadata check
    info = provider.get_info()
    assert info.name == "groq"
    assert info.default_model_name == "llama-3.3-70b-versatile"
    assert info.is_available is True


# ---------------------------------------------------------------------------
# Tests: GroqProvider Mocked Completion Generation
# ---------------------------------------------------------------------------


def test_groq_provider_generate_response_text(monkeypatch):
    """Test GroqProvider.generate_response parses text completion using mocked httpx."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_mock_key")

    mock_groq_json = {
        "id": "chatcmpl-test-101",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Files successfully organized into Documents.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 25,
            "completion_tokens": 12,
            "total_tokens": 37,
        },
    }

    mock_response = httpx.Response(status_code=200, json=mock_groq_json)

    with patch.object(httpx.Client, "post", return_value=mock_response) as mock_post:
        provider = GroqProvider()
        prompt = Prompt(
            system_prompt="You are a helpful assistant.",
            user_prompt="Organize my files",
        )
        req = AIRequest(request_id="req-groq-01", prompt=prompt)

        res = provider.generate_response(req)

        assert isinstance(res, AIResponse)
        assert res.response_id == "chatcmpl-test-101"
        assert res.text == "Files successfully organized into Documents."
        assert res.finish_reason == FinishReason.STOP
        assert res.usage_stats["total_tokens"] == 37
        assert res.provider_name == "groq"
        assert mock_post.called


def test_groq_provider_generate_response_tool_calls(monkeypatch):
    """Test GroqProvider parses tool calls from API response payload."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_mock_key")

    mock_tool_json = {
        "id": "chatcmpl-tool-202",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_12345",
                            "type": "function",
                            "function": {
                                "name": "move_file",
                                "arguments": json.dumps({"source": "/tmp/a.txt", "dest": "/tmp/b.txt"}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 30, "completion_tokens": 15, "total_tokens": 45},
    }

    mock_response = httpx.Response(status_code=200, json=mock_tool_json)

    with patch.object(httpx.Client, "post", return_value=mock_response):
        provider = GroqProvider()
        prompt = Prompt(user_prompt="Move file a.txt to b.txt")
        req = AIRequest(request_id="req-tool-1", prompt=prompt)

        res = provider.generate_response(req)
        assert res.finish_reason == FinishReason.TOOL_CALLS
        assert len(res.tool_calls) == 1
        tc = res.tool_calls[0]
        assert tc.call_id == "call_12345"
        assert tc.tool_name == "move_file"
        assert tc.arguments == {"source": "/tmp/a.txt", "dest": "/tmp/b.txt"}


def test_groq_provider_health_check_success(monkeypatch):
    """Test GroqProvider.health_check returns healthy status when HTTP GET 200."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_mock_key")

    mock_models_json = {"data": [{"id": "llama-3.3-70b-versatile"}]}
    mock_response = httpx.Response(status_code=200, json=mock_models_json)

    with patch.object(httpx.Client, "get", return_value=mock_response):
        provider = GroqProvider()
        health = provider.health_check()

        assert health["status"] == "ok"
        assert health["healthy"] is True
        assert "latency_ms" in health
        assert health["provider"] == "groq"


# ---------------------------------------------------------------------------
# Tests: ProviderManager Priorities, Default Selection, & Failover
# ---------------------------------------------------------------------------


class MockFailoverProvider(GroqProvider):
    """Mock Provider subclass for failover testing."""

    def __init__(self, name: str, should_fail: bool = False, response_text: str = "Success"):
        config = ProviderConfig(
            provider_name=name,
            model_name="mock-model",
            api_key_env=f"{name.upper()}_KEY",
        )
        super().__init__(config)
        self.should_fail = should_fail
        self.response_text = response_text

    def is_available(self) -> bool:
        return True

    def generate_response(self, request: AIRequest) -> AIResponse:
        if self.should_fail:
            raise ProviderUnavailableError(self.config.provider_name, reason="Simulated network failure")
        return AIResponse(
            response_id="res-failover",
            request_id=request.request_id,
            text=self.response_text,
            provider_name=self.config.provider_name,
        )


def test_provider_manager_priorities_and_defaults():
    """Test priority sorting and default provider setting in ProviderManager."""
    manager = ProviderManager()

    p_low = MockFailoverProvider(name="low_priority")
    p_high = MockFailoverProvider(name="high_priority")
    p_med = MockFailoverProvider(name="med_priority")

    manager.register_provider(p_low, priority=10)
    manager.register_provider(p_high, priority=100, is_default=True)
    manager.register_provider(p_med, priority=50)

    # Check default provider
    assert manager.get_default_provider() == p_high

    # Check priority ordering
    ordered = manager.get_providers_by_priority()
    assert len(ordered) == 3
    assert ordered[0] == p_high
    assert ordered[1] == p_med
    assert ordered[2] == p_low


def test_provider_manager_failover_execution():
    """Test ProviderManager.generate_response_with_failover falls back when primary provider fails."""
    manager = ProviderManager()

    primary_failing = MockFailoverProvider(name="primary_failing", should_fail=True)
    secondary_working = MockFailoverProvider(name="secondary_working", response_text="Fallback Answer")

    manager.register_provider(primary_failing, priority=100)
    manager.register_provider(secondary_working, priority=50)

    req = AIRequest(request_id="req-failover-1", prompt=Prompt(user_prompt="Hello"))

    # Should attempt primary (priority 100), catch failure, and succeed on secondary (priority 50)
    res = manager.generate_response_with_failover(req)
    assert res.text == "Fallback Answer"
    assert res.provider_name == "secondary_working"


def test_provider_manager_failover_all_failed():
    """Test ProviderManager raises ProviderUnavailableError when all providers fail."""
    manager = ProviderManager()

    p1 = MockFailoverProvider(name="p1", should_fail=True)
    p2 = MockFailoverProvider(name="p2", should_fail=True)

    manager.register_provider(p1, priority=10)
    manager.register_provider(p2, priority=5)

    req = AIRequest(request_id="req-failover-fail", prompt=Prompt(user_prompt="Hello"))

    with pytest.raises(ProviderUnavailableError) as exc_info:
        manager.generate_response_with_failover(req)

    assert "failover_exhausted" in str(exc_info.value)
