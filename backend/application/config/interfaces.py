"""Configuration Runtime Interfaces (Phase 14.3.2).

Defines Abstract Base Classes (ABCs) establishing explicit design contracts for
IConfigurationSource, ConfigurationRuntime, ConfigurationProvider, ConfigurationManager,
ConfigurationValidator, and ConfigurationDiagnostics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationEntry,
    ConfigurationHealth,
    ConfigurationRuntimeState,
    ConfigurationSnapshot,
    ConfigurationSourceType,
    ConfigurationStatistics,
    SourceHealth,
    SourceStatistics,
)


class IConfigurationSource(ABC):
    """Abstract interface for individual configuration sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Get unique name of the configuration source."""
        raise NotImplementedError

    @property
    @abstractmethod
    def source_type(self) -> ConfigurationSourceType:
        """Get source provider type."""
        raise NotImplementedError

    @property
    @abstractmethod
    def priority(self) -> int:
        """Get numerical priority level (higher numbers take precedence)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Check if source is enabled."""
        raise NotImplementedError

    @abstractmethod
    def contains(self, key: str) -> bool:
        """Check if configuration key exists in source."""
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value for key from source."""
        raise NotImplementedError

    @abstractmethod
    def keys(self) -> Tuple[str, ...]:
        """Get all keys in source."""
        raise NotImplementedError

    @abstractmethod
    def values(self) -> Tuple[Any, ...]:
        """Get all values in source."""
        raise NotImplementedError

    @abstractmethod
    def items(self) -> Tuple[Tuple[str, Any], ...]:
        """Get all (key, value) pairs in source."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> SourceHealth:
        """Get health status of source."""
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> SourceStatistics:
        """Get metrics of source."""
        raise NotImplementedError


class IConfigurationDiagnostics(ABC):
    """Abstract interface for Configuration Diagnostics provider."""

    @abstractmethod
    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get diagnostics snapshot."""
        raise NotImplementedError


class IConfigurationValidator(ABC):
    """Abstract interface for Configuration Validator engine."""

    @abstractmethod
    def validate(self) -> bool:
        """Validate loaded configuration against schemas and constraints."""
        raise NotImplementedError


class IConfigurationManager(ABC):
    """Abstract interface for Configuration Manager operations."""

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration property value by key."""
        raise NotImplementedError

    @abstractmethod
    def get_entry(self, key: str) -> Optional[ConfigurationEntry]:
        """Get detailed ConfigurationEntry with source metadata."""
        raise NotImplementedError

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a configuration key exists."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all merged configuration key-value pairs."""
        raise NotImplementedError

    @abstractmethod
    def create_snapshot(self) -> ConfigurationSnapshot:
        """Create an immutable merged configuration snapshot."""
        raise NotImplementedError

    @abstractmethod
    def register_source(self, source: IConfigurationSource) -> bool:
        """Register a configuration source."""
        raise NotImplementedError

    @abstractmethod
    def unregister_source(self, source_name: str) -> bool:
        """Unregister a configuration source by name."""
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
