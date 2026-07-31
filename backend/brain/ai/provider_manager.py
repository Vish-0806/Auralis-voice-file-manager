"""ProviderManager for managing AIProvider lifecycles and failover (Phase 10.1 & Phase 10.2).

Handles registration, default provider selection, priority ordering, provider failover,
querying, and diagnostic health monitoring.
"""

from typing import Dict, List, Optional, Any, Tuple

from brain.ai.exceptions import (
    ProviderNotFoundError,
    ProviderRegistrationError,
    ProviderUnavailableError,
)
from brain.ai.interfaces import AIProvider
from brain.ai.ai_models import AIRequest, AIResponse, ProviderInfo


class ProviderManager:
    """Registry and manager for AI providers supporting priorities and automatic failover."""

    def __init__(self) -> None:
        self._providers: Dict[str, AIProvider] = {}
        self._priorities: Dict[str, int] = {}
        self._active_provider_name: Optional[str] = None
        self._default_provider_name: Optional[str] = None

    def register_provider(
        self,
        provider: AIProvider,
        set_active: bool = False,
        priority: int = 0,
        is_default: bool = False,
    ) -> None:
        """Register an AIProvider instance with priority and default settings.

        Args:
            provider: Concrete implementation of AIProvider.
            set_active: If True, set this provider as active.
            priority: Priority weighting (higher value = higher preference in failover).
            is_default: If True, set this provider as default.

        Raises:
            ProviderRegistrationError: If provider is invalid or already registered.
        """
        if not isinstance(provider, AIProvider):
            raise ProviderRegistrationError("Object does not implement AIProvider interface.")

        info = provider.get_info()
        name = info.name.lower()

        if name in self._providers:
            raise ProviderRegistrationError(f"Provider '{info.name}' is already registered.")

        self._providers[name] = provider
        self._priorities[name] = priority

        if set_active or self._active_provider_name is None:
            self._active_provider_name = name

        if is_default or self._default_provider_name is None:
            self._default_provider_name = name

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider by name.

        Args:
            name: Provider name string.

        Raises:
            ProviderNotFoundError: If provider name is not found.
        """
        key = name.lower()
        if key not in self._providers:
            raise ProviderNotFoundError(name)

        del self._providers[key]
        self._priorities.pop(key, None)

        if self._active_provider_name == key:
            self._active_provider_name = next(iter(self._providers.keys()), None)

        if self._default_provider_name == key:
            self._default_provider_name = next(iter(self._providers.keys()), None)

    def get_provider(self, name: str) -> AIProvider:
        """Retrieve a registered provider by name."""
        key = name.lower()
        if key not in self._providers:
            raise ProviderNotFoundError(name)
        return self._providers[key]

    def set_active_provider(self, name: str) -> None:
        """Set the active provider by name."""
        key = name.lower()
        if key not in self._providers:
            raise ProviderNotFoundError(name)

        provider = self._providers[key]
        if not provider.is_available():
            raise ProviderUnavailableError(name, reason="Provider reported not available.")

        self._active_provider_name = key

    def get_active_provider(self) -> Optional[AIProvider]:
        """Get the currently active AIProvider instance."""
        if self._active_provider_name is None:
            return None
        return self._providers.get(self._active_provider_name)

    def set_default_provider(self, name: str) -> None:
        """Set the default provider by name."""
        key = name.lower()
        if key not in self._providers:
            raise ProviderNotFoundError(name)
        self._default_provider_name = key

    def get_default_provider(self) -> Optional[AIProvider]:
        """Get the default AIProvider instance."""
        if self._default_provider_name is None:
            return None
        return self._providers.get(self._default_provider_name)

    def set_provider_priority(self, name: str, priority: int) -> None:
        """Set the priority weight for a registered provider."""
        key = name.lower()
        if key not in self._providers:
            raise ProviderNotFoundError(name)
        self._priorities[key] = priority

    def get_providers_by_priority(self, available_only: bool = False) -> List[AIProvider]:
        """Get registered providers sorted by priority in descending order.

        Args:
            available_only: If True, filter out unavailable providers.

        Returns:
            List of AIProvider instances ordered from highest to lowest priority.
        """
        sorted_keys = sorted(
            self._providers.keys(),
            key=lambda k: self._priorities.get(k, 0),
            reverse=True,
        )

        result: List[AIProvider] = []
        for key in sorted_keys:
            provider = self._providers[key]
            if available_only and not provider.is_available():
                continue
            result.append(provider)

        return result

    def generate_response_with_failover(self, request: AIRequest) -> AIResponse:
        """Attempt completion generation using available providers in priority order.

        If a provider fails or is unavailable, attempts execution on the next highest priority provider.

        Args:
            request: Incoming AIRequest model.

        Returns:
            AIResponse from the first successful provider.

        Raises:
            ProviderUnavailableError: If all providers fail or no available providers are found.
        """
        providers = self.get_providers_by_priority(available_only=True)
        if not providers:
            raise ProviderUnavailableError(
                "all_providers",
                reason="No registered providers are currently available for failover execution.",
            )

        failover_errors: List[str] = []

        for provider in providers:
            info = provider.get_info()
            try:
                return provider.generate_response(request)
            except Exception as exc:
                failover_errors.append(f"[{info.name}]: {exc}")

        raise ProviderUnavailableError(
            "failover_exhausted",
            reason=f"All available providers failed during failover execution: {'; '.join(failover_errors)}",
        )

    def list_providers(self) -> List[ProviderInfo]:
        """List metadata for all registered providers."""
        return [provider.get_info() for provider in self._providers.values()]

    def health_status(self) -> Dict[str, Any]:
        """Collect comprehensive health and priority metrics across all registered providers."""
        status: Dict[str, Any] = {
            "active_provider": self._active_provider_name,
            "default_provider": self._default_provider_name,
            "total_registered": len(self._providers),
            "providers": {},
        }

        for name, provider in self._providers.items():
            try:
                status["providers"][name] = {
                    "priority": self._priorities.get(name, 0),
                    "available": provider.is_available(),
                    "health": provider.health_check(),
                }
            except Exception as exc:
                status["providers"][name] = {
                    "priority": self._priorities.get(name, 0),
                    "available": False,
                    "error": str(exc),
                }

        return status
