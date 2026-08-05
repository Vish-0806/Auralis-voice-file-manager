"""API Runtime Interfaces (Phase 15.1).

Defines Abstract Base Classes (ABCs) establishing design contracts for the API Runtime
and API Provider.
"""

from abc import ABC, abstractmethod
from typing import Optional

from backend.application.api.models import (
    ApiCapabilities,
    ApiConfiguration,
    ApiDiagnostics,
    ApiHealth,
    ApiState,
    ApiStatistics,
)


class IApiRuntime(ABC):
    """Abstract interface for the API Runtime."""

    @abstractmethod
    def initialize(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Initialize the API runtime.

        Args:
            config: Optional API configuration override.

        Returns:
            ApiState: Updated state snapshot.

        Raises:
            ApiInitializationException: If initialization fails.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ApiState:
        """Shutdown the API runtime safely.

        Returns:
            ApiState: Updated state snapshot.

        Raises:
            ApiRuntimeException: If shutdown fails.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Restart the API runtime.

        Args:
            config: Optional API configuration override.

        Returns:
            ApiState: Updated state snapshot.

        Raises:
            ApiRuntimeException: If restart fails.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ApiHealth:
        """Get current health assessment of the API runtime.

        Returns:
            ApiHealth: Health evaluation snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ApiStatistics:
        """Get current aggregate metrics and statistics.

        Returns:
            ApiStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ApiCapabilities:
        """Get capabilities supported by the API runtime.

        Returns:
            ApiCapabilities: Declared capability flags.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ApiDiagnostics:
        """Get diagnostic information and telemetry.

        Returns:
            ApiDiagnostics: System diagnostics snapshot.
        """
        raise NotImplementedError


class IApiProvider(ABC):
    """Abstract interface for the API Provider."""

    @abstractmethod
    def initialize(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Initialize the API provider.

        Args:
            config: Optional API configuration override.

        Returns:
            ApiState: Updated state snapshot.

        Raises:
            ApiProviderException: If initialization fails.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ApiState:
        """Shutdown the API provider safely.

        Returns:
            ApiState: Updated state snapshot.

        Raises:
            ApiProviderException: If shutdown fails.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Restart the API provider.

        Args:
            config: Optional API configuration override.

        Returns:
            ApiState: Updated state snapshot.

        Raises:
            ApiProviderException: If restart fails.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ApiHealth:
        """Get health status of the API provider.

        Returns:
            ApiHealth: Health evaluation snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ApiStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            ApiStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ApiCapabilities:
        """Get declared capabilities.

        Returns:
            ApiCapabilities: Declared capability flags.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ApiDiagnostics:
        """Get diagnostic telemetry for the provider.

        Returns:
            ApiDiagnostics: System diagnostics snapshot.
        """
        raise NotImplementedError
