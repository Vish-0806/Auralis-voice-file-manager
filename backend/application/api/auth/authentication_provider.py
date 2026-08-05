"""API Authentication Provider Implementation (Phase 15.4).

Thread-safe authentication provider aggregating IdentityManager, SessionManager,
and AuthorizationManager with full lifecycle management, health evaluation,
statistics tracking, and diagnostic telemetry.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.auth.authorization_manager import (
    AuthorizationManager,
)
from backend.application.api.auth.identity_manager import IdentityManager
from backend.application.api.auth.interfaces import (
    IAuthenticationProvider,
    IAuthorizationManager,
    IIdentityManager,
    ISessionManager,
)
from backend.application.api.auth.models import (
    AuthenticationCapabilities,
    AuthenticationDiagnostics,
    AuthenticationHealth,
    AuthenticationRuntimeState,
    AuthenticationStatistics,
)
from backend.application.api.auth.session_manager import SessionManager

logger = logging.getLogger(__name__)


class AuthenticationProvider(IAuthenticationProvider):
    """Production thread-safe authentication provider aggregating security components."""

    def __init__(
        self,
        identity_manager: Optional[IIdentityManager] = None,
        session_manager: Optional[ISessionManager] = None,
        authorization_manager: Optional[IAuthorizationManager] = None,
        capabilities: Optional[AuthenticationCapabilities] = None,
    ) -> None:
        """Initialize AuthenticationProvider using Constructor Dependency Injection.

        Args:
            identity_manager: Optional IIdentityManager implementation instance.
            session_manager: Optional ISessionManager implementation instance.
            authorization_manager: Optional IAuthorizationManager implementation instance.
            capabilities: Optional AuthenticationCapabilities instance.
        """
        self._lock = RLock()
        self._identity_manager = identity_manager or IdentityManager()
        self._session_manager = session_manager or SessionManager()
        self._authorization_manager = authorization_manager or AuthorizationManager()
        self._capabilities = capabilities or AuthenticationCapabilities()

        self._status = AuthenticationRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> AuthenticationHealth:
        """Initialize the authentication provider and transition to READY state.

        Returns:
            AuthenticationHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status in (
                AuthenticationRuntimeState.INITIALIZING,
                AuthenticationRuntimeState.READY,
            ):
                return self.health()

            self._status = AuthenticationRuntimeState.INITIALIZING
            logger.info("AuthenticationProvider transitioning to INITIALIZING state.")

            self._status = AuthenticationRuntimeState.READY
            self._total_initializations += 1
            logger.info("AuthenticationProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> AuthenticationHealth:
        """Shutdown the authentication provider safely and transition to STOPPED state.

        Returns:
            AuthenticationHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status == AuthenticationRuntimeState.STOPPED:
                return self.health()

            self._status = AuthenticationRuntimeState.STOPPING
            logger.info("AuthenticationProvider transitioning to STOPPING state.")

            self._status = AuthenticationRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("AuthenticationProvider successfully stopped.")
            return self.health()

    def restart(self) -> AuthenticationHealth:
        """Restart the authentication provider by shutting down if active, then initializing.

        Returns:
            AuthenticationHealth: Updated health snapshot.
        """
        with self._lock:
            logger.info("AuthenticationProvider restarting...")
            if self._status != AuthenticationRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> AuthenticationHealth:
        """Get health status evaluation snapshot.

        Returns:
            AuthenticationHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                AuthenticationRuntimeState.READY,
                AuthenticationRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Auth provider is in state: {self._status.value}",)

            return AuthenticationHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "identities_count": self._identity_manager.count_identities(),
                    "sessions_count": self._session_manager.count_sessions(),
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> AuthenticationStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            AuthenticationStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            total_ids = self._identity_manager.count_identities()
            active_sess = len(self._session_manager.list_active_sessions())

            session_telemetry = {}
            if hasattr(self._session_manager, "get_session_telemetry"):
                session_telemetry = getattr(self._session_manager, "get_session_telemetry")()

            auth_telemetry = {}
            if hasattr(self._authorization_manager, "get_authorization_telemetry"):
                auth_telemetry = getattr(
                    self._authorization_manager, "get_authorization_telemetry"
                )()

            return AuthenticationStatistics(
                total_identities=total_ids,
                active_sessions=active_sess,
                expired_sessions=session_telemetry.get("expired_sessions", 0),
                revoked_sessions=session_telemetry.get("revoked_sessions", 0),
                granted_authorizations=auth_telemetry.get("granted_authorizations", 0),
                denied_authorizations=auth_telemetry.get("denied_authorizations", 0),
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> AuthenticationCapabilities:
        """Get declared capabilities.

        Returns:
            AuthenticationCapabilities: Immutable capabilities snapshot.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> AuthenticationDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            AuthenticationDiagnostics: Immutable diagnostics snapshot.
        """
        with self._lock:
            total_ids = self._identity_manager.count_identities()
            active_sess = len(self._session_manager.list_active_sessions())
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Total Identities: {total_ids}",
                f"Active Sessions: {active_sess}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return AuthenticationDiagnostics(
                state=self._status,
                identities_count=total_ids,
                active_sessions_count=active_sess,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_identity_manager(self) -> IIdentityManager:
        """Get encapsulated identity manager.

        Returns:
            IIdentityManager: Identity manager.
        """
        with self._lock:
            return self._identity_manager

    def get_session_manager(self) -> ISessionManager:
        """Get encapsulated session manager.

        Returns:
            ISessionManager: Session manager.
        """
        with self._lock:
            return self._session_manager

    def get_authorization_manager(self) -> IAuthorizationManager:
        """Get encapsulated authorization manager.

        Returns:
            IAuthorizationManager: Authorization manager.
        """
        with self._lock:
            return self._authorization_manager
