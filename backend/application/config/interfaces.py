"""Configuration Runtime Interfaces (Phase 14.3.1).

Defines Abstract Base Classes (ABCs) establishing explicit design contracts for
ConfigurationRuntime, ConfigurationProvider, ConfigurationManager, ConfigurationValidator,
and ConfigurationDiagnostics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationRuntimeState,
    ConfigurationStatistics,
)


class IConfigurationDiagnostics(ABC):
    """Abstract interface for Configuration Diagnostics provider."""

    @abstractmethod
    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get diagnostics snapshot.

        Returns:
            ConfigurationDiagnostics: Diagnostics snapshot model.
        """
        raise NotImplementedError


class IConfigurationValidator(ABC):
    """Abstract interface for Configuration Validator engine."""

    @abstractmethod
    def validate(self) -> bool:
        """Validate loaded configuration against schemas and constraints.

        Returns:
            bool: True if configuration is valid.
        """
        raise NotImplementedError


class IConfigurationManager(ABC):
    """Abstract interface for Configuration Manager operations."""

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration property value by key.

        Args:
            key: Configuration key string.
            default: Optional default value if key is missing.

        Returns:
            Any: Configuration property value.
        """
        raise NotImplementedError

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: Configuration key string.

        Returns:
            bool: True if key exists.
        """
        raise NotImplementedError


class IConfigurationProvider(ABC):
    """Abstract interface for Configuration Provider runtime coordination."""

    @abstractmethod
    def initialize(self) -> ConfigurationRuntimeState:
        """Initialize provider runtime state."""
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ConfigurationRuntimeState:
        """Shutdown provider runtime operations."""
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> ConfigurationRuntimeState:
        """Restart provider runtime operations."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ConfigurationHealth:
        """Get health assessment snapshot."""
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ConfigurationStatistics:
        """Get statistics metrics snapshot."""
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ConfigurationCapabilities:
        """Get capabilities snapshot."""
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get diagnostics snapshot."""
        raise NotImplementedError

    @abstractmethod
    def get_context(self) -> ConfigurationContext:
        """Get execution context snapshot."""
        raise NotImplementedError


class IConfigurationRuntime(ABC):
    """Abstract interface for Configuration Runtime lifecycle & execution."""

    @abstractmethod
    def initialize(self) -> ConfigurationRuntimeState:
        """Initialize configuration runtime."""
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ConfigurationRuntimeState:
        """Shutdown configuration runtime."""
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> ConfigurationRuntimeState:
        """Restart configuration runtime."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ConfigurationHealth:
        """Get health assessment snapshot."""
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ConfigurationStatistics:
        """Get statistics metrics snapshot."""
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ConfigurationCapabilities:
        """Get capabilities snapshot."""
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get diagnostics snapshot."""
        raise NotImplementedError

    @abstractmethod
    def context(self) -> ConfigurationContext:
        """Get configuration context snapshot."""
        raise NotImplementedError
