"""Policy Engine implementation (Phase 11.8).

Applies configurable execution security policies (ALLOW, DENY, REQUIRE_CONFIRMATION,
READ_ONLY, SANDBOX_ONLY) per operation category.
"""

import threading
from typing import Dict

from brain.os.security.interfaces import IPolicyEngine
from brain.os.security.security_models import (
    OperationCategory,
    PermissionLevel,
    PermissionResult,
    SecurityDecisionType,
    SecurityRequest,
)


class PolicyEngine(IPolicyEngine):
    """Thread-safe configurable policy engine."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._category_policies: Dict[OperationCategory, SecurityDecisionType] = {
            OperationCategory.FILESYSTEM: SecurityDecisionType.ALLOW,
            OperationCategory.PROCESS: SecurityDecisionType.ALLOW,
            OperationCategory.APPLICATION: SecurityDecisionType.ALLOW,
            OperationCategory.DESKTOP: SecurityDecisionType.ALLOW,
            OperationCategory.WINDOW: SecurityDecisionType.ALLOW,
            OperationCategory.DEVICE: SecurityDecisionType.ALLOW,
            OperationCategory.SYSTEM: SecurityDecisionType.ALLOW,
        }

    def set_policy(
        self, category: OperationCategory, decision: SecurityDecisionType
    ) -> None:
        """Configure default policy decision for an operation category."""
        with self._lock:
            self._category_policies[category] = decision

    def evaluate_policy(
        self, request: SecurityRequest, perm_result: PermissionResult
    ) -> SecurityDecisionType:
        """Evaluate execution policy decision for a request."""
        if not perm_result.granted:
            return SecurityDecisionType.DENY

        with self._lock:
            cat_decision = self._category_policies.get(
                request.category, SecurityDecisionType.ALLOW
            )

        if cat_decision == SecurityDecisionType.READ_ONLY:
            if request.requested_permission in (PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.ADMIN):
                return SecurityDecisionType.DENY
            return SecurityDecisionType.ALLOW

        return cat_decision
