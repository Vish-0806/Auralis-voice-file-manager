"""Assistant Provider implementation for Auralis (Phase 13.1).

Aggregates assistant services, sub-runtimes (Phases 9–12), health monitoring,
statistics collection, session management, and capabilities.
Enforces constructor dependency injection and thread safety via threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.assistant.exceptions import AssistantInitializationError, AssistantSessionError
from brain.assistant.interfaces import (
    IAssistantHealthMonitor,
    IAssistantProvider,
    IAssistantSessionManager,
    IAssistantStatisticsCollector,
)
from brain.assistant.models import (
    AssistantCapabilities,
    AssistantConfiguration,
    AssistantContext,
    AssistantHealth,
    AssistantSession,
    AssistantStateEnum,
    AssistantStatistics,
)

logger = logging.getLogger(__name__)


class DefaultSessionManager(IAssistantSessionManager):
    """Internal thread-safe session manager implementation."""

    def __init__(self, lock: threading.RLock) -> None:
        self._lock = lock
        self._sessions: Dict[str, AssistantSession] = {}

    def create_session(self, context: Optional[Any] = None) -> AssistantSession:
        with self._lock:
            if isinstance(context, AssistantContext):
                ctx = context
            elif isinstance(context, dict):
                ctx = AssistantContext(**context)
            else:
                ctx = AssistantContext()

            session = AssistantSession(
                session_id=ctx.session_id,
                context=ctx,
                active=True,
                created_at=datetime.now(timezone.utc),
                last_accessed_at=datetime.now(timezone.utc),
            )
            self._sessions[session.session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[AssistantSession]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.active:
                updated_session = session.model_copy(
                    update={"last_accessed_at": datetime.now(timezone.utc)}
                )
                self._sessions[session_id] = updated_session
                return updated_session
            return session

    def close_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                self._sessions[session_id] = session.model_copy(update={"active": False})
                return True
            return False

    def list_sessions(self) -> Dict[str, AssistantSession]:
        with self._lock:
            return dict(self._sessions)

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()


class AssistantProvider(IAssistantProvider):
    """Aggregate assistant services coordinator using constructor dependency injection only."""

    def __init__(
        self,
        brain_runtime: Optional[Any] = None,
        ai_runtime: Optional[Any] = None,
        os_runtime: Optional[Any] = None,
        execution_runtime: Optional[Any] = None,
        configuration: Optional[AssistantConfiguration] = None,
        session_manager: Optional[IAssistantSessionManager] = None,
        health_monitor: Optional[IAssistantHealthMonitor] = None,
        statistics_collector: Optional[IAssistantStatisticsCollector] = None,
        capabilities: Optional[AssistantCapabilities] = None,
    ) -> None:
        """Initialize AssistantProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._brain_runtime = brain_runtime
        self._ai_runtime = ai_runtime
        self._os_runtime = os_runtime
        self._execution_runtime = execution_runtime
        self._configuration = configuration or AssistantConfiguration()

        self._session_manager = session_manager or DefaultSessionManager(self._lock)
        self._health_monitor = health_monitor
        self._statistics_collector = statistics_collector
        self._custom_capabilities = capabilities

        self._initialized = False
        self._start_time: Optional[float] = None

        # Statistics state
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._total_latency_ms = 0.0
        self._total_sessions_created = 0

    # ------------------------------------------------------------------
    # Properties for Injected Dependencies
    # ------------------------------------------------------------------

    @property
    def brain_runtime(self) -> Optional[Any]:
        with self._lock:
            return self._brain_runtime

    @property
    def ai_runtime(self) -> Optional[Any]:
        with self._lock:
            return self._ai_runtime

    @property
    def os_runtime(self) -> Optional[Any]:
        with self._lock:
            return self._os_runtime

    @property
    def execution_runtime(self) -> Optional[Any]:
        with self._lock:
            return self._execution_runtime

    @property
    def configuration(self) -> AssistantConfiguration:
        with self._lock:
            return self._configuration

    @property
    def session_manager(self) -> IAssistantSessionManager:
        with self._lock:
            return self._session_manager

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Lifecycle Management
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize provider resources and underlying subsystem runtimes."""
        with self._lock:
            if self._initialized:
                return

            try:
                # Optionally initialize injected sub-runtimes if they present an initialize method
                for name, runtime in [
                    ("brain_runtime", self._brain_runtime),
                    ("ai_runtime", self._ai_runtime),
                    ("os_runtime", self._os_runtime),
                    ("execution_runtime", self._execution_runtime),
                ]:
                    if runtime is not None and hasattr(runtime, "initialize") and callable(runtime.initialize):
                        try:
                            runtime.initialize()
                        except Exception as exc:
                            logger.warning("Failed to initialize sub-runtime %s: %s", name, exc)

                self._initialized = True
                self._start_time = time.time()
                logger.info("AssistantProvider initialized successfully")
            except Exception as exc:
                self._initialized = False
                raise AssistantInitializationError(f"AssistantProvider initialization failed: {exc}") from exc

    def shutdown(self) -> None:
        """Gracefully shut down provider resources and sub-runtimes."""
        with self._lock:
            if not self._initialized:
                return

            for name, runtime in [
                ("execution_runtime", self._execution_runtime),
                ("os_runtime", self._os_runtime),
                ("ai_runtime", self._ai_runtime),
                ("brain_runtime", self._brain_runtime),
            ]:
                if runtime is not None and hasattr(runtime, "shutdown") and callable(runtime.shutdown):
                    try:
                        runtime.shutdown()
                    except Exception as exc:
                        logger.warning("Failed to shutdown sub-runtime %s: %s", name, exc)

            self._initialized = False
            self._start_time = None
            logger.info("AssistantProvider shutdown complete")

    # ------------------------------------------------------------------
    # Capabilities, Health, and Statistics
    # ------------------------------------------------------------------

    def get_capabilities(self) -> AssistantCapabilities:
        """Expose assistant capability specification."""
        with self._lock:
            if self._custom_capabilities is not None:
                return self._custom_capabilities

            providers: List[str] = []
            if self._brain_runtime is not None:
                providers.append("brain_runtime")
            if self._ai_runtime is not None:
                providers.append("ai_runtime")
            if self._os_runtime is not None:
                providers.append("os_runtime")
            if self._execution_runtime is not None:
                providers.append("execution_runtime")

            return AssistantCapabilities(
                brain_integration=self._brain_runtime is not None or self._configuration.enable_brain,
                ai_integration=self._ai_runtime is not None or self._configuration.enable_ai,
                os_integration=self._os_runtime is not None or self._configuration.enable_os,
                execution_integration=self._execution_runtime is not None or self._configuration.enable_execution,
                streaming_supported=False,
                voice_supported=False,
                conversation_supported=False,
                supported_providers=providers,
                custom_capabilities=self._configuration.custom_settings.get("capabilities", {}),
            )

    def get_health(self) -> AssistantHealth:
        """Expose aggregated assistant health."""
        with self._lock:
            if self._health_monitor is not None:
                return self._health_monitor.check_health()

            subsystems = {
                "brain_runtime": self._brain_runtime is not None,
                "ai_runtime": self._ai_runtime is not None,
                "os_runtime": self._os_runtime is not None,
                "execution_runtime": self._execution_runtime is not None,
                "session_manager": self._session_manager is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("AssistantProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return AssistantHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={"provider_initialized": self._initialized},
            )

    def get_statistics(self) -> AssistantStatistics:
        """Expose assistant runtime statistics."""
        with self._lock:
            if self._statistics_collector is not None:
                return self._statistics_collector.collect_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            avg_latency = (self._total_latency_ms / self._total_requests) if self._total_requests > 0 else 0.0
            active_sess_count = len([s for s in self._session_manager.list_sessions().values() if s.active])

            return AssistantStatistics(
                total_requests=self._total_requests,
                successful_requests=self._successful_requests,
                failed_requests=self._failed_requests,
                active_sessions=active_sess_count,
                total_sessions_created=self._total_sessions_created,
                average_latency_ms=avg_latency,
                uptime_seconds=uptime,
                subsystem_metrics={},
                metadata={"provider_name": self._configuration.name},
            )

    # ------------------------------------------------------------------
    # Metrics & Session Helpers
    # ------------------------------------------------------------------

    def record_request(self, duration_ms: float = 0.0, success: bool = True) -> None:
        """Record an executed request metric thread-safely."""
        with self._lock:
            self._total_requests += 1
            if success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1
            self._total_latency_ms += duration_ms

    def create_session(self, context: Optional[Any] = None) -> AssistantSession:
        """Create a new assistant session via the session manager."""
        with self._lock:
            session = self._session_manager.create_session(context)
            self._total_sessions_created += 1
            return session

    def get_session(self, session_id: str) -> Optional[AssistantSession]:
        """Retrieve active assistant session by ID."""
        with self._lock:
            return self._session_manager.get_session(session_id)

    def close_session(self, session_id: str) -> bool:
        """Close an assistant session by ID."""
        with self._lock:
            return self._session_manager.close_session(session_id)

    def clear(self) -> None:
        """Clear provider statistics and active sessions."""
        with self._lock:
            self._total_requests = 0
            self._successful_requests = 0
            self._failed_requests = 0
            self._total_latency_ms = 0.0
            self._total_sessions_created = 0
            if hasattr(self._session_manager, "clear"):
                self._session_manager.clear()  # type: ignore[union-attr]
