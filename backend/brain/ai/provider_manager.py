"""ProviderManager for managing AIProvider lifecycles (Phase 10.1).

Handles registration, selection, query, and health checking of AI providers.
No concrete providers integrated yet.
"""

from typing import Dict, List, Optional, Any

from brain.ai.exceptions import (
    ProviderNotFoundError,
    ProviderRegistrationError,
    ProviderUnavailableError,
)
from brain.ai.interfaces import AIProvider
from brain.ai.ai_models import ProviderInfo


class ProviderManager:
    """Registry and manager for AI providers in the Auralis architecture."""

    def __init__(self) -> None:
        self._providers: Dict[str, AIProvider] = {}
        self._active_provider_name: Optional[str] = None

    def register_provider(self, provider: AIProvider, set_active: bool = False) -> None:
        """Register an AIProvider instance.

        Args:
            provider: Concrete implementation of AIProvider.
            set_active: If True, set this provider as the active provider.

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

        if set_active or self._active_provider_name is None:
            self._active_provider_name = name

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

        if self._active_provider_name == key:
            self._active_provider_name = next(iter(self._providers.keys()), None)

    def get_provider(self, name: str) -> AIProvider:
        """Retrieve a registered provider by name.

        Args:
            name: Provider name string.

        Returns:
            AIProvider instance.

        Raises:
            ProviderNotFoundError: If provider name is not found.
        """
        key = name.lower()
        if key not in self._providers:
            raise ProviderNotFoundError(name)
        return self._providers[key]

    def set_active_provider(self, name: str) -> None:
        """Set the active provider by name.

        Args:
            name: Provider name string.

        Raises:
            ProviderNotFoundError: If provider name is not found.
            ProviderUnavailableError: If provider is registered but unavailable.
        """
        key = name.lower()
        if key not in self._providers:
            raise ProviderNotFoundError(name)

        provider = self._providers[key]
        if not provider.is_available():
            raise ProviderUnavailableError(name, reason="Provider reported not available.")

        self._active_provider_name = key

    def get_active_provider(self) -> Optional[AIProvider]:
        """Get the currently active AIProvider instance.

        Returns:
            Active AIProvider instance, or None if no providers are registered.
        """
        if self._active_provider_name is None:
            return None
        return self._providers.get(self._active_provider_name)

    def list_providers(self) -> List[ProviderInfo]:
        """List metadata for all registered providers.

        Returns:
            List of ProviderInfo metadata models.
        """
        return [provider.get_info() for provider in self._providers.values()]

    def health_status(self) -> Dict[str, Any]:
        """Collect health status across all registered providers.

        Returns:
            Dictionary mapping provider names to their health status diagnostic outputs.
        """
        status: Dict[str, Any] = {
            "active_provider": self._active_provider_name,
            "total_registered": len(self._providers),
            "providers": {},
        }

        for name, provider in self._providers.items():
            try:
                status["providers"][name] = {
                    "available": provider.is_available(),
                    "health": provider.health_check(),
                }
            except Exception as exc:
                status["providers"][name] = {
                    "available": False,
                    "error": str(exc),
                }

        return status
