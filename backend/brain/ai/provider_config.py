"""Provider Configuration model and environment loaders for Auralis AI subsystem (Phase 10.2).

Defines ProviderConfig and configuration factory functions.
"""

import os
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ProviderConfig(BaseModel):
    """Configuration settings for a concrete AI Provider."""

    model_config = ConfigDict(frozen=True)

    provider_name: str
    model_name: str
    api_key_env: str
    base_url: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    timeout: float = 30.0
    supports_streaming: bool = False
    supports_tools: bool = True
    supports_reasoning: bool = False
    supports_images: bool = False
    enabled: bool = True


def load_provider_config_from_env(
    provider_name: str,
    default_model: str,
    default_api_key_env: str,
    default_base_url: Optional[str] = None,
    prefix: Optional[str] = None,
) -> ProviderConfig:
    """Construct ProviderConfig dynamically by reading environment variables with optional fallback defaults.

    Args:
        provider_name: Name of the provider (e.g. 'groq').
        default_model: Fallback model identifier.
        default_api_key_env: Name of environment variable holding API key.
        default_base_url: Fallback API endpoint URL.
        prefix: Optional prefix for env vars (e.g. 'GROQ_').

    Returns:
        Configured ProviderConfig model instance.
    """
    env_prefix = prefix or f"{provider_name.upper()}_"

    model_name = os.getenv(f"{env_prefix}MODEL", default_model)
    base_url = os.getenv(f"{env_prefix}BASE_URL", default_base_url)
    api_key_env = os.getenv(f"{env_prefix}API_KEY_ENV", default_api_key_env)

    temp_str = os.getenv(f"{env_prefix}TEMPERATURE")
    temperature = float(temp_str) if temp_str else 0.7

    top_p_str = os.getenv(f"{env_prefix}TOP_P")
    top_p = float(top_p_str) if top_p_str else 1.0

    max_tokens_str = os.getenv(f"{env_prefix}MAX_TOKENS")
    max_tokens = int(max_tokens_str) if max_tokens_str else None

    timeout_str = os.getenv(f"{env_prefix}TIMEOUT")
    timeout = float(timeout_str) if timeout_str else 30.0

    enabled_str = os.getenv(f"{env_prefix}ENABLED")
    enabled = enabled_str.lower() not in ("false", "0", "no") if enabled_str else True

    return ProviderConfig(
        provider_name=provider_name,
        model_name=model_name,
        api_key_env=api_key_env,
        base_url=base_url,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        timeout=timeout,
        supports_streaming=False,
        supports_tools=True,
        supports_reasoning=False,
        supports_images=False,
        enabled=enabled,
    )


def get_groq_default_config() -> ProviderConfig:
    """Return default ProviderConfig for Groq AI provider."""
    return load_provider_config_from_env(
        provider_name="groq",
        default_model="llama-3.3-70b-versatile",
        default_api_key_env="GROQ_API_KEY",
        default_base_url="https://api.groq.com/openai/v1",
        prefix="GROQ_",
    )
