"""API Authorization Manager Implementation (Phase 15.4).

Thread-safe deterministic authorization engine evaluating RBAC permissions, roles,
and claims without HTTP, external identity providers, or network calls.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict

from backend.application.api.auth.interfaces import IAuthorizationManager
from backend.application.api.auth.models import (
    AuthorizationDecision,
    AuthorizationResult,
    Identity,
)

logger = logging.getLogger(__name__)


class AuthorizationManager(IAuthorizationManager):
    """Thread-safe authorization engine evaluating roles, claims, and permissions."""

    def __init__(self) -> None:
        """Initialize AuthorizationManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._granted_authorizations = 0
        self._denied_authorizations = 0

    def evaluate(
        self, identity: Identity, resource: str, action: str
    ) -> AuthorizationDecision:
        """Evaluate permission check for an identity on a resource and action.

        Args:
            identity: Target Identity instance.
            resource: Target resource string.
            action: Requested action string.

        Returns:
            AuthorizationDecision: Immutable evaluation decision object.
        """
        with self._lock:
            if not identity.is_active:
                self._denied_authorizations += 1
                return AuthorizationDecision(
                    result=AuthorizationResult.DENIED,
                    identity_id=identity.identity_id,
                    resource=resource,
                    action=action,
                    reason="Identity is inactive",
                    evaluated_at=datetime.now(timezone.utc),
                )

            for role in identity.roles:
                for perm in role.permissions:
                    resource_match = perm.resource == "*" or perm.resource == resource
                    action_match = perm.action == "*" or perm.action == action

                    if resource_match and action_match:
                        self._granted_authorizations += 1
                        logger.info(
                            "Granted access to identity '%s' for resource '%s' action '%s' via role '%s'.",
                            identity.identity_id,
                            resource,
                            action,
                            role.name,
                        )
                        return AuthorizationDecision(
                            result=AuthorizationResult.GRANTED,
                            identity_id=identity.identity_id,
                            resource=resource,
                            action=action,
                            reason=f"Permission granted via role '{role.name}' (perm: {perm.name})",
                            evaluated_at=datetime.now(timezone.utc),
                        )

            self._denied_authorizations += 1
            logger.info(
                "Denied access to identity '%s' for resource '%s' action '%s'.",
                identity.identity_id,
                resource,
                action,
            )
            return AuthorizationDecision(
                result=AuthorizationResult.DENIED,
                identity_id=identity.identity_id,
                resource=resource,
                action=action,
                reason="No matching permission granted in identity roles",
                evaluated_at=datetime.now(timezone.utc),
            )

    def evaluate_role(
        self, identity: Identity, role_name: str
    ) -> AuthorizationDecision:
        """Evaluate if an identity possesses a specific role by name.

        Args:
            identity: Target Identity instance.
            role_name: Target role name string.

        Returns:
            AuthorizationDecision: Immutable evaluation decision object.
        """
        with self._lock:
            if not identity.is_active:
                self._denied_authorizations += 1
                return AuthorizationDecision(
                    result=AuthorizationResult.DENIED,
                    identity_id=identity.identity_id,
                    resource=f"role:{role_name}",
                    action="has_role",
                    reason="Identity is inactive",
                    evaluated_at=datetime.now(timezone.utc),
                )

            has_role = any(r.name == role_name for r in identity.roles)
            if has_role:
                self._granted_authorizations += 1
                return AuthorizationDecision(
                    result=AuthorizationResult.GRANTED,
                    identity_id=identity.identity_id,
                    resource=f"role:{role_name}",
                    action="has_role",
                    reason=f"Identity asserts role '{role_name}'",
                    evaluated_at=datetime.now(timezone.utc),
                )

            self._denied_authorizations += 1
            return AuthorizationDecision(
                result=AuthorizationResult.DENIED,
                identity_id=identity.identity_id,
                resource=f"role:{role_name}",
                action="has_role",
                reason=f"Identity does not possess role '{role_name}'",
                evaluated_at=datetime.now(timezone.utc),
            )

    def evaluate_claim(
        self, identity: Identity, claim_key: str, claim_value: str
    ) -> AuthorizationDecision:
        """Evaluate if an identity asserts a claim key and value pair.

        Args:
            identity: Target Identity instance.
            claim_key: Claim key string.
            claim_value: Claim value string.

        Returns:
            AuthorizationDecision: Immutable evaluation decision object.
        """
        with self._lock:
            if not identity.is_active:
                self._denied_authorizations += 1
                return AuthorizationDecision(
                    result=AuthorizationResult.DENIED,
                    identity_id=identity.identity_id,
                    resource=f"claim:{claim_key}",
                    action="assert_claim",
                    reason="Identity is inactive",
                    evaluated_at=datetime.now(timezone.utc),
                )

            has_claim = any(
                c.key == claim_key and c.value == claim_value for c in identity.claims
            )
            if has_claim:
                self._granted_authorizations += 1
                return AuthorizationDecision(
                    result=AuthorizationResult.GRANTED,
                    identity_id=identity.identity_id,
                    resource=f"claim:{claim_key}",
                    action="assert_claim",
                    reason=f"Identity asserts claim '{claim_key}={claim_value}'",
                    evaluated_at=datetime.now(timezone.utc),
                )

            self._denied_authorizations += 1
            return AuthorizationDecision(
                result=AuthorizationResult.DENIED,
                identity_id=identity.identity_id,
                resource=f"claim:{claim_key}",
                action="assert_claim",
                reason=f"Identity does not assert claim '{claim_key}={claim_value}'",
                evaluated_at=datetime.now(timezone.utc),
            )

    def get_authorization_telemetry(self) -> Dict[str, int]:
        """Get internal evaluation telemetry counters under lock."""
        with self._lock:
            return {
                "granted_authorizations": self._granted_authorizations,
                "denied_authorizations": self._denied_authorizations,
                "total_evaluations": self._granted_authorizations + self._denied_authorizations,
            }
