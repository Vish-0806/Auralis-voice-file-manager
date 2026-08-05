"""API Policy Engine Implementation (Phase 15.8).

Thread-safe policy engine evaluating protection policies, priority orders,
and client rate limit rules without middleware or networking dependencies.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, Optional, Tuple
import uuid

from backend.application.api.protection.exceptions import ProtectionException
from backend.application.api.protection.interfaces import (
    IPolicyEngine,
    IRateLimiter,
)
from backend.application.api.protection.models import (
    ApiPolicy,
    PolicyDecision,
    ProtectionContext,
    ProtectionDecision,
)
from backend.application.api.protection.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class PolicyEngine(IPolicyEngine):
    """Thread-safe policy engine evaluating ApiPolicy definitions and generating PolicyDecision models."""

    def __init__(self, rate_limiter: Optional[IRateLimiter] = None) -> None:
        """Initialize PolicyEngine using Constructor Dependency Injection.

        Args:
            rate_limiter: Optional IRateLimiter implementation instance.
        """
        self._lock = RLock()
        self._rate_limiter = rate_limiter or RateLimiter()
        self._policies: Dict[str, ApiPolicy] = {}

        self._total_evaluations = 0
        self._allowed_requests = 0
        self._throttled_requests = 0
        self._rejected_requests = 0

    def register_policy(self, policy: ApiPolicy) -> ApiPolicy:
        """Register a new API protection policy.

        Args:
            policy: Immutable ApiPolicy instance.

        Returns:
            ApiPolicy: Registered policy model.

        Raises:
            ProtectionException: If policy_id is already registered.
        """
        with self._lock:
            if policy.policy_id in self._policies:
                raise ProtectionException(
                    f"API policy with ID '{policy.policy_id}' is already registered."
                )

            self._policies[policy.policy_id] = policy
            # Also register embedded rules into rate limiter if present
            for rule in policy.rules:
                if self._rate_limiter.lookup_rule(rule.rule_id) is None:
                    self._rate_limiter.register_rule(rule)

            logger.info("Registered API policy ID '%s' (%s).", policy.policy_id, policy.name)
            return policy

    def unregister_policy(self, policy_id: str) -> Optional[ApiPolicy]:
        """Unregister a policy by policy ID.

        Args:
            policy_id: Unique policy identifier.

        Returns:
            Optional[ApiPolicy]: Removed policy if present, else None.
        """
        with self._lock:
            policy = self._policies.pop(policy_id, None)
            if policy is not None:
                logger.info("Unregistered API policy ID '%s'.", policy_id)
            return policy

    def lookup_policy(self, policy_id: str) -> Optional[ApiPolicy]:
        """Look up a policy by ID.

        Args:
            policy_id: Unique policy identifier.

        Returns:
            Optional[ApiPolicy]: Policy model if found, else None.
        """
        with self._lock:
            return self._policies.get(policy_id)

    def evaluate_client(self, context: ProtectionContext) -> PolicyDecision:
        """Evaluate incoming client request context against registered policies in priority order.

        Args:
            context: Immutable ProtectionContext model.

        Returns:
            PolicyDecision: Resulting policy decision.
        """
        with self._lock:
            self._total_evaluations += 1
            decision_id = f"pdec_{uuid.uuid4().hex[:8]}"

            # Sort active policies by priority (ascending: lower number = higher priority)
            active_policies = sorted(
                [p for p in self._policies.values() if p.is_enabled],
                key=lambda p: p.priority,
            )

            client_id = context.client.client_id

            for policy in active_policies:
                # Check embedded rate limit rules
                for rule in policy.rules:
                    rl_decision = self._rate_limiter.evaluate_rate_limit(
                        client_id=client_id, rule_id=rule.rule_id
                    )
                    if not rl_decision.is_allowed:
                        action = (
                            ProtectionDecision.THROTTLE
                            if policy.decision != ProtectionDecision.REJECT
                            else ProtectionDecision.REJECT
                        )

                        if action == ProtectionDecision.THROTTLE:
                            self._throttled_requests += 1
                        else:
                            self._rejected_requests += 1

                        logger.warning(
                            "Policy '%s' triggered %s for client '%s' on rule '%s'.",
                            policy.policy_id,
                            action.value,
                            client_id,
                            rule.rule_id,
                        )

                        return PolicyDecision(
                            decision_id=decision_id,
                            client_id=client_id,
                            policy_id=policy.policy_id,
                            action=action,
                            reason=f"Rate limit exceeded for rule '{rule.name}' in policy '{policy.name}'.",
                            rate_limit_decision=rl_decision,
                            evaluated_at=datetime.now(timezone.utc),
                        )

                # Explicit policy decision check
                if policy.decision == ProtectionDecision.REJECT:
                    self._rejected_requests += 1
                    return PolicyDecision(
                        decision_id=decision_id,
                        client_id=client_id,
                        policy_id=policy.policy_id,
                        action=ProtectionDecision.REJECT,
                        reason=f"Explicit rejection by policy '{policy.name}'.",
                        evaluated_at=datetime.now(timezone.utc),
                    )

                if policy.decision == ProtectionDecision.ALLOW:
                    self._allowed_requests += 1
                    return PolicyDecision(
                        decision_id=decision_id,
                        client_id=client_id,
                        policy_id=policy.policy_id,
                        action=ProtectionDecision.ALLOW,
                        reason=f"Explicit allow by policy '{policy.name}'.",
                        evaluated_at=datetime.now(timezone.utc),
                    )

            self._allowed_requests += 1
            return PolicyDecision(
                decision_id=decision_id,
                client_id=client_id,
                policy_id=active_policies[0].policy_id if active_policies else None,
                action=ProtectionDecision.ALLOW,
                reason="Default allow policy evaluation.",
                evaluated_at=datetime.now(timezone.utc),
            )

    def list_policies(self) -> Tuple[ApiPolicy, ...]:
        """List all registered policies.

        Returns:
            Tuple[ApiPolicy, ...]: Immutable tuple of policies.
        """
        with self._lock:
            return tuple(self._policies.values())

    def count_policies(self) -> int:
        """Get total count of registered policies.

        Returns:
            int: Policy count.
        """
        with self._lock:
            return len(self._policies)

    def clear(self) -> None:
        """Clear all policies from the policy engine."""
        with self._lock:
            self._policies.clear()
            logger.info("PolicyEngine cleared.")

    def get_engine_telemetry(self) -> Dict[str, int]:
        """Get internal policy engine telemetry counters under lock."""
        with self._lock:
            return {
                "total_evaluations": self._total_evaluations,
                "allowed_requests": self._allowed_requests,
                "throttled_requests": self._throttled_requests,
                "rejected_requests": self._rejected_requests,
                "registered_policies_count": len(self._policies),
            }
