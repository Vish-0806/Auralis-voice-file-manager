"""Application Service Provider (Phase 14.1).

High-level provider encapsulating configured runtime instance, configuration,
context, and capability definitions.
"""

from threading import RLock
from typing import Optional

from backend.application.interfaces import IApplicationProvider, IApplicationRuntime
from backend.application.models import (
    ApplicationCapabilities,
    ApplicationConfiguration,
    ApplicationContext,
)


class ApplicationProvider(IApplicationProvider):
    """Provider exposing application runtime, configuration, context, and capabilities."""

    def __init__(
        self,
        runtime: Optional[IApplicationRuntime] = None,
        config: Optional[ApplicationConfiguration] = None,
    ) -> None:
        """Initialize ApplicationProvider with Constructor Dependency Injection.

        Args:
            runtime: Optional application runtime instance.
            config: Optional application configuration instance.
        """
        self._lock = RLock()
        self._runtime = runtime
        self._config = config

    def get_runtime(self) -> IApplicationRuntime:
        """Get active application runtime instance.

        Returns:
            IApplicationRuntime: Configured application runtime instance.

        Raises:
            NotImplementedError: Pending business logic implementation.
        """
        raise NotImplementedError

    def get_configuration(self) -> ApplicationConfiguration:
        """Get active application configuration.

        Returns:
            ApplicationConfiguration: Active configuration instance.

        Raises:
            NotImplementedError: Pending business logic implementation.
        """
        raise NotImplementedError

    def get_context(self) -> ApplicationContext:
        """Get active application execution context.

        Returns:
            ApplicationContext: Active application context.

        Raises:
            NotImplementedError: Pending business logic implementation.
        """
        raise NotImplementedError

    def get_capabilities(self) -> ApplicationCapabilities:
        """Get active application capabilities.

        Returns:
            ApplicationCapabilities: Declared application capabilities.

        Raises:
            NotImplementedError: Pending business logic implementation.
        """
        raise NotImplementedError
