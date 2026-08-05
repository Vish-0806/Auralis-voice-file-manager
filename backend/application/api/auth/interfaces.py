"""API Authentication & Authorization Interfaces (Phase 15.4).

Defines Abstract Base Classes (ABCs) establishing design contracts for the Identity
Manager, Session Manager, Authorization Manager, Authentication Provider, and Authentication Runtime.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from backend.application.api.auth.models import (
    AuthenticationCapabilities,
    AuthenticationDiagnostics,
    AuthenticationHealth,
    AuthenticationSession,
    AuthenticationStatistics,
    AuthorizationDecision,
    Claim,
    Identity,
    Principal,
    Role,
)


class IIdentityManager(ABC):
    """Abstract interface for the Identity Manager."""

    @abstractmethod
    def register_identity(self, identity: Identity) -> Identity:
        """Register a new identity.

        Args:
            identity: Immutable Identity instance.

        Returns:
            Identity: Registered identity.

        Raises:
            IdentityException: If identity registration fails or duplicate ID exists.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_identity(self, identity_id: str) -> Optional[Identity]:
        """Look up an identity by ID.

        Args:
            identity_id: Unique identity identifier.

        Returns:
            Optional[Identity]: Identity model if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_principal(self, principal_id: str) -> Optional[Principal]:
        """Look up a security principal by principal ID.

        Args:
            principal_id: Unique principal identifier.

        Returns:
            Optional[Principal]: Principal model if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def assign_role(self, identity_id: str, role: Role) -> Optional[Identity]:
        """Assign a role to an identity.

        Args:
            identity_id: Target identity ID.
            role: Role to assign.

        Returns:
            Optional[Identity]: Updated Identity if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def add_claim(self, identity_id: str, claim: Claim) -> Optional[Identity]:
        """Add a claim assertion to an identity.

        Args:
            identity_id: Target identity ID.
            claim: Claim assertion.

        Returns:
            Optional[Identity]: Updated Identity if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_identities(self) -> Tuple[Identity, ...]:
        """List all registered identities.

        Returns:
            Tuple[Identity, ...]: Tuple of registered identities.
        """
        raise NotImplementedError

    @abstractmethod
    def count_identities(self) -> int:
        """Get total count of registered identities.

        Returns:
            int: Identity count.
        """
        raise NotImplementedError


class ISessionManager(ABC):
    """Abstract interface for the Session Manager."""

    @abstractmethod
    def create_session(
        self, identity_id: str, ttl_seconds: Optional[float] = 3600.0
    ) -> AuthenticationSession:
        """Create a new authentication session for an identity.

        Args:
            identity_id: Target identity ID.
            ttl_seconds: Optional session time-to-live in seconds.

        Returns:
            AuthenticationSession: Created session snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[AuthenticationSession]:
        """Get a session by session ID, checking expiration state.

        Args:
            session_id: Unique session identifier.

        Returns:
            Optional[AuthenticationSession]: Session snapshot if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def revoke_session(self, session_id: str) -> Optional[AuthenticationSession]:
        """Revoke an active authentication session.

        Args:
            session_id: Target session ID.

        Returns:
            Optional[AuthenticationSession]: Updated session if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def expire_session(self, session_id: str) -> Optional[AuthenticationSession]:
        """Expire an active authentication session.

        Args:
            session_id: Target session ID.

        Returns:
            Optional[AuthenticationSession]: Updated session if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_active_sessions(self) -> Tuple[AuthenticationSession, ...]:
        """List all currently active (unexpired, non-revoked) sessions.

        Returns:
            Tuple[AuthenticationSession, ...]: Tuple of active sessions.
        """
        raise NotImplementedError

    @abstractmethod
    def count_sessions(self) -> int:
        """Get total count of sessions managed.

        Returns:
            int: Total session count.
        """
        raise NotImplementedError


class IAuthorizationManager(ABC):
    """Abstract interface for the Authorization Manager engine."""

    @abstractmethod
    def evaluate(
        self, identity: Identity, resource: str, action: str
    ) -> AuthorizationDecision:
        """Evaluate permission check for an identity on a resource and action.

        Args:
            identity: Target Identity instance.
            resource: Target resource string.
            action: Requested action string.

        Returns:
            AuthorizationDecision: Immutable evaluation decision.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate_role(
        self, identity: Identity, role_name: str
    ) -> AuthorizationDecision:
        """Evaluate if an identity possesses a specific role by name.

        Args:
            identity: Target Identity instance.
            role_name: Role name string.

        Returns:
            AuthorizationDecision: Immutable evaluation decision.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate_claim(
        self, identity: Identity, claim_key: str, claim_value: str
    ) -> AuthorizationDecision:
        """Evaluate if an identity asserts a claim key/value pair.

        Args:
            identity: Target Identity instance.
            claim_key: Claim key.
            claim_value: Claim value.

        Returns:
            AuthorizationDecision: Immutable evaluation decision.
        """
        raise NotImplementedError


class IAuthenticationProvider(ABC):
    """Abstract interface for the Authentication Provider."""

    @abstractmethod
    def initialize(self) -> AuthenticationHealth:
        """Initialize the authentication provider.

        Returns:
            AuthenticationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> AuthenticationHealth:
        """Shutdown the authentication provider safely.

        Returns:
            AuthenticationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> AuthenticationHealth:
        """Restart the authentication provider.

        Returns:
            AuthenticationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> AuthenticationHealth:
        """Get health evaluation snapshot.

        Returns:
            AuthenticationHealth: Health evaluation.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> AuthenticationStatistics:
        """Get aggregate statistics.

        Returns:
            AuthenticationStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> AuthenticationCapabilities:
        """Get declared capabilities.

        Returns:
            AuthenticationCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> AuthenticationDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            AuthenticationDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_identity_manager(self) -> IIdentityManager:
        """Get encapsulated identity manager.

        Returns:
            IIdentityManager: Identity manager.
        """
        raise NotImplementedError

    @abstractmethod
    def get_session_manager(self) -> ISessionManager:
        """Get encapsulated session manager.

        Returns:
            ISessionManager: Session manager.
        """
        raise NotImplementedError

    @abstractmethod
    def get_authorization_manager(self) -> IAuthorizationManager:
        """Get encapsulated authorization manager.

        Returns:
            IAuthorizationManager: Authorization manager.
        """
        raise NotImplementedError


class IAuthenticationRuntime(ABC):
    """Abstract interface for the Authentication Runtime."""

    @abstractmethod
    def initialize(self) -> AuthenticationHealth:
        """Initialize the authentication runtime.

        Returns:
            AuthenticationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> AuthenticationHealth:
        """Shutdown the authentication runtime safely.

        Returns:
            AuthenticationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> AuthenticationHealth:
        """Restart the authentication runtime.

        Returns:
            AuthenticationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> AuthenticationHealth:
        """Get health snapshot.

        Returns:
            AuthenticationHealth: Health evaluation.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> AuthenticationStatistics:
        """Get aggregate statistics.

        Returns:
            AuthenticationStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> AuthenticationCapabilities:
        """Get declared capabilities.

        Returns:
            AuthenticationCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> AuthenticationDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            AuthenticationDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IAuthenticationProvider:
        """Get encapsulated authentication provider.

        Returns:
            IAuthenticationProvider: Authentication provider.
        """
        raise NotImplementedError
