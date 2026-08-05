"""API Protection & Rate Limiting Interfaces (Phase 15.8).

Defines Abstract Base Classes (ABCs) establishing design contracts for the Rate Limiter,
Policy Engine, Violation Tracker, Protection Provider, and Protection Runtime.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from backend.application.api.protection.models import (
    ApiPolicy,
    PolicyDecision,
    ProtectionCapabilities,
    ProtectionContext,
    ProtectionDiagnostics,
    ProtectionHealth,
    ProtectionStatistics,
    RateLimitDecision,
    RateLimitRule,
    ViolationRecord,
)


class IRateLimiter(ABC):
    """Abstract interface for the API Rate Limiter."""

    @abstractmethod
    def register_rule(self, rule: RateLimitRule) -> RateLimitRule:
        """Register a new rate limit rule.

        Args:
            rule: Immutable RateLimitRule instance.

        Returns:
            RateLimitRule: Registered rule model.

        Raises:
            RateLimitException: If rule registration fails or rule_id exists.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        """Unregister a rate limit rule by rule ID.

        Args:
            rule_id: Unique rule identifier.

        Returns:
            Optional[RateLimitRule]: Removed rule if present, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        """Look up a rate limit rule by ID.

        Args:
            rule_id: Unique rule identifier.

        Returns:
            Optional[RateLimitRule]: Rule model if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate_rate_limit(
        self, client_id: str, rule_id: str
    ) -> RateLimitDecision:
        """Evaluate rate limit quota for a client against a registered rule ID.

        Args:
            client_id: Target client identifier.
            rule_id: Target registered rule ID.

        Returns:
            RateLimitDecision: Result snapshot of rate limit evaluation.
        """
        raise NotImplementedError

    @abstractmethod
    def list_rules(self) -> Tuple[RateLimitRule, ...]:
        """List all registered rate limit rules.

        Returns:
            Tuple[RateLimitRule, ...]: Tuple of registered rules.
        """
        raise NotImplementedError

    @abstractmethod
    def count_rules(self) -> int:
        """Get total count of registered rate limit rules.

        Returns:
            int: Rule count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all registered rules and active quota tracking state."""
        raise NotImplementedError


class IPolicyEngine(ABC):
    """Abstract interface for the API Policy Engine."""

    @abstractmethod
    def register_policy(self, policy: ApiPolicy) -> ApiPolicy:
        """Register a new API protection policy.

        Args:
            policy: Immutable ApiPolicy instance.

        Returns:
            ApiPolicy: Registered policy model.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_policy(self, policy_id: str) -> Optional[ApiPolicy]:
        """Unregister a policy by policy ID.

        Args:
            policy_id: Unique policy identifier.

        Returns:
            Optional[ApiPolicy]: Removed policy if present, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_policy(self, policy_id: str) -> Optional[ApiPolicy]:
        """Look up a policy by ID.

        Args:
            policy_id: Unique policy identifier.

        Returns:
            Optional[ApiPolicy]: Policy model if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate_client(self, context: ProtectionContext) -> PolicyDecision:
        """Evaluate incoming client request context against registered policies.

        Args:
            context: Immutable ProtectionContext model.

        Returns:
            PolicyDecision: Evaluated policy decision.
        """
        raise NotImplementedError

    @abstractmethod
    def list_policies(self) -> Tuple[ApiPolicy, ...]:
        """List all registered policies.

        Returns:
            Tuple[ApiPolicy, ...]: Tuple of policies.
        """
        raise NotImplementedError

    @abstractmethod
    def count_policies(self) -> int:
        """Get total count of registered policies.

        Returns:
            int: Policy count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all policies from the policy engine."""
        raise NotImplementedError


class IViolationTracker(ABC):
    """Abstract interface for the Violation Tracker."""

    @abstractmethod
    def record_violation(self, violation: ViolationRecord) -> ViolationRecord:
        """Record a new violation event.

        Args:
            violation: Immutable ViolationRecord instance.

        Returns:
            ViolationRecord: Recorded violation model.
        """
        raise NotImplementedError

    @abstractmethod
    def list_violations(
        self, client_id: Optional[str] = None
    ) -> Tuple[ViolationRecord, ...]:
        """List violation records, optionally filtered by client ID.

        Args:
            client_id: Optional client ID filter.

        Returns:
            Tuple[ViolationRecord, ...]: Tuple of matching violation records.
        """
        raise NotImplementedError

    @abstractmethod
    def is_client_in_cooldown(self, client_id: str) -> bool:
        """Check if a client is currently in an active cooldown window.

        Args:
            client_id: Unique client identifier.

        Returns:
            bool: True if client is in active cooldown, else False.
        """
        raise NotImplementedError

    @abstractmethod
    def count_violations(self) -> int:
        """Get total count of recorded violation records.

        Returns:
            int: Violation count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear_expired_violations(self) -> int:
        """Purge expired violation records past their cooldown period.

        Returns:
            int: Count of purged records.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all violation records from the tracker."""
        raise NotImplementedError


class IProtectionProvider(ABC):
    """Abstract interface for the Protection Provider."""

    @abstractmethod
    def initialize(self) -> ProtectionHealth:
        """Initialize the protection provider.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ProtectionHealth:
        """Shutdown the protection provider safely.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> ProtectionHealth:
        """Restart the protection provider.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ProtectionHealth:
        """Get health evaluation snapshot.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ProtectionStatistics:
        """Get aggregate statistics.

        Returns:
            ProtectionStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ProtectionCapabilities:
        """Get declared capabilities.

        Returns:
            ProtectionCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ProtectionDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            ProtectionDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_rate_limiter(self) -> IRateLimiter:
        """Get encapsulated rate limiter.

        Returns:
            IRateLimiter: Rate limiter.
        """
        raise NotImplementedError

    @abstractmethod
    def get_policy_engine(self) -> IPolicyEngine:
        """Get encapsulated policy engine.

        Returns:
            IPolicyEngine: Policy engine.
        """
        raise NotImplementedError

    @abstractmethod
    def get_violation_tracker(self) -> IViolationTracker:
        """Get encapsulated violation tracker.

        Returns:
            IViolationTracker: Violation tracker.
        """
        raise NotImplementedError


class IProtectionRuntime(ABC):
    """Abstract interface for the Protection Runtime."""

    @abstractmethod
    def initialize(self) -> ProtectionHealth:
        """Initialize the protection runtime.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ProtectionHealth:
        """Shutdown the protection runtime safely.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> ProtectionHealth:
        """Restart the protection runtime.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ProtectionHealth:
        """Get health evaluation snapshot.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ProtectionStatistics:
        """Get aggregate statistics.

        Returns:
            ProtectionStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ProtectionCapabilities:
        """Get declared capabilities.

        Returns:
            ProtectionCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ProtectionDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            ProtectionDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IProtectionProvider:
        """Get encapsulated protection provider.

        Returns:
            IProtectionProvider: Protection provider.
        """
        raise NotImplementedError
