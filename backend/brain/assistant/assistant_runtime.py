"""Assistant Runtime Coordinator for Auralis (Phase 13.1).

Highest-level orchestration layer managing assistant status, health reporting, statistics,
provider registration, and thread-safe lifecycle operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, Optional

from brain.assistant.assistant_provider import AssistantProvider
from brain.assistant.exceptions import (
    AssistantInitializationError,
    AssistantRuntimeError,
)
from brain.assistant.interfaces import IAssistantProvider, IAssistantRuntime
from brain.assistant.models import (
    AssistantCapabilities,
    AssistantConfiguration,
    AssistantHealth,
    AssistantState,
    AssistantStateEnum,
    AssistantStatistics,
    AssistantStatus,
)

logger = logging.getLogger(__name__)


class AssistantRuntime(IAssistantRuntime):
    """Thread-safe core Assistant Runtime orchestrating highest-level assistant services."""

    def __init__(
        self,
        provider: Optional[IAssistantProvider] = None,
        configuration: Optional[AssistantConfiguration] = None,
    ) -> None:
        """Initialize AssistantRuntime with optional provider and configuration."""
        self._lock = threading.RLock()
        self._configuration = configuration or AssistantConfiguration()
        self._provider = provider
        self._state_enum = AssistantStateEnum.UNINITIALIZED
        self._start_time: Optional[float] = None
        self._initialized_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Properties & Accessors
    # ------------------------------------------------------------------

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._state_enum in (AssistantStateEnum.READY, AssistantStateEnum.RUNNING)

    @property
    def state(self) -> AssistantState:
        with self._lock:
            return AssistantState(
                state=self._state_enum,
                healthy=self._state_enum in (AssistantStateEnum.READY, AssistantStateEnum.RUNNING),
                initialized_at=self._initialized_at,
                last_updated=datetime.now(timezone.utc),
                details={"provider_registered": self._provider is not None},
            )

    @property
    def configuration(self) -> AssistantConfiguration:
        with self._lock:
            return self._configuration

    def get_provider(self) -> Optional[IAssistantProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IAssistantProvider) -> None:
        """Register an IAssistantProvider implementation thread-safely."""
        with self._lock:
            if not isinstance(provider, IAssistantProvider):
                raise TypeError("Provider must implement IAssistantProvider interface")
            self._provider = provider
            logger.debug("Registered assistant provider: %s", provider)

    # ------------------------------------------------------------------
    # Lifecycle Management
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize the Assistant Runtime environment.

        Raises:
            AssistantInitializationError: If initialization fails.
        """
        with self._lock:
            if self.is_initialized:
                return

            self._state_enum = AssistantStateEnum.INITIALIZING

            try:
                if self._provider is None:
                    self._provider = AssistantProvider(configuration=self._configuration)

                if not self._provider.is_initialized:
                    self._provider.initialize()

                self._state_enum = AssistantStateEnum.READY
                self._start_time = time.time()
                self._initialized_at = datetime.now(timezone.utc)
                logger.info("AssistantRuntime initialized successfully (state=%s)", self._state_enum)
            except Exception as exc:
                self._state_enum = AssistantStateEnum.ERROR
                logger.error("AssistantRuntime initialization failed: %s", exc)
                raise AssistantInitializationError(f"AssistantRuntime initialization error: {exc}") from exc

    def shutdown(self) -> None:
        """Gracefully shut down the Assistant Runtime environment."""
        with self._lock:
            if self._state_enum in (AssistantStateEnum.STOPPED, AssistantStateEnum.UNINITIALIZED):
                return

            self._state_enum = AssistantStateEnum.STOPPING

            try:
                if self._provider is not None and self._provider.is_initialized:
                    self._provider.shutdown()
            except Exception as exc:
                logger.warning("Error during provider shutdown: %s", exc)
            finally:
                self._state_enum = AssistantStateEnum.STOPPED
                self._start_time = None
                logger.info("AssistantRuntime shutdown complete")

    def restart(self) -> None:
        """Restart the Assistant Runtime environment."""
        with self._lock:
            self.shutdown()
            self.initialize()

    def clear(self) -> None:
        """Reset runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._state_enum = AssistantStateEnum.UNINITIALIZED
            self._start_time = None
            self._initialized_at = None

    # ------------------------------------------------------------------
    # Status, Health, Statistics & Capabilities Reporting
    # ------------------------------------------------------------------

    def get_status(self) -> AssistantStatus:
        """Return current status of the Assistant Runtime."""
        with self._lock:
            uptime = 0.0
            if self._start_time is not None and self.is_initialized:
                uptime = max(0.0, time.time() - self._start_time)

            active_sess = 0
            if self._provider is not None:
                stats = self._provider.get_statistics()
                active_sess = stats.active_sessions

            healthy = self.is_initialized and (self._provider.get_health().healthy if self._provider else True)

            return AssistantStatus(
                state=self._state_enum,
                healthy=healthy,
                provider_count=1 if self._provider is not None else 0,
                active_sessions=active_sess,
                uptime_seconds=uptime,
                version=self._configuration.version,
                details={
                    "name": self._configuration.name,
                    "provider_registered": self._provider is not None,
                },
            )

    def get_health(self) -> AssistantHealth:
        """Return aggregated health of the Assistant Runtime."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self.is_initialized
            return AssistantHealth(
                status="READY" if healthy else self._state_enum.value,
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered or runtime uninitialized"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> AssistantStatistics:
        """Return execution and performance statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self.is_initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return AssistantStatistics(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                active_sessions=0,
                total_sessions_created=0,
                average_latency_ms=0.0,
                uptime_seconds=uptime,
                subsystem_metrics={},
                metadata={},
            )

    def get_capabilities(self) -> AssistantCapabilities:
        """Return capability specifications."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_capabilities()
            return AssistantCapabilities()
