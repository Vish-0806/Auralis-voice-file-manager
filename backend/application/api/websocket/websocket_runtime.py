"""API WebSocket Runtime Coordinator Implementation (Phase 15.7).

Thread-safe, provider-independent API WebSocket Runtime coordinator managing lifecycle
operations and delegating queries to the underlying WebSocketProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.websocket.interfaces import (
    IWebSocketProvider,
    IWebSocketRuntime,
)
from backend.application.api.websocket.models import (
    WebSocketCapabilities,
    WebSocketDiagnostics,
    WebSocketHealth,
    WebSocketStatistics,
)
from backend.application.api.websocket.websocket_provider import (
    WebSocketProvider,
)

logger = logging.getLogger(__name__)


class WebSocketRuntime(IWebSocketRuntime):
    """Production thread-safe WebSocket runtime coordinator."""

    def __init__(self, provider: Optional[IWebSocketProvider] = None) -> None:
        """Initialize WebSocketRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IWebSocketProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or WebSocketProvider()

    def initialize(self) -> WebSocketHealth:
        """Initialize the WebSocket runtime and underlying provider.

        Returns:
            WebSocketHealth: Health snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing WebSocketRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> WebSocketHealth:
        """Shutdown the WebSocket runtime and underlying provider safely.

        Returns:
            WebSocketHealth: Health snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down WebSocketRuntime.")
            return self._provider.shutdown()

    def restart(self) -> WebSocketHealth:
        """Restart the WebSocket runtime and underlying provider.

        Returns:
            WebSocketHealth: Health snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting WebSocketRuntime.")
            return self._provider.restart()

    def health(self) -> WebSocketHealth:
        """Get health evaluation snapshot from underlying provider.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> WebSocketStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            WebSocketStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> WebSocketCapabilities:
        """Get capabilities from underlying provider.

        Returns:
            WebSocketCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> WebSocketDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            WebSocketDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IWebSocketProvider:
        """Get encapsulated IWebSocketProvider instance.

        Returns:
            IWebSocketProvider: Underlying WebSocket provider.
        """
        with self._lock:
            return self._provider
