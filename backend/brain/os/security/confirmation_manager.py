"""Confirmation Manager implementation (Phase 11.8).

Determines whether explicit user confirmation is required based on configurable policies
(ALWAYS, NEVER, DANGEROUS_ONLY, ADMIN_ONLY, DESTRUCTIVE_ONLY) and risk assessments.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional

from brain.os.security.interfaces import IConfirmationManager
from brain.os.security.security_models import (
    ConfirmationPolicy,
    ConfirmationRequest,
    PermissionResult,
    RiskAssessment,
    RiskLevel,
    SecurityRequest,
)


class ConfirmationManager(IConfirmationManager):
    """Provides user confirmation evaluation and request generation."""

    def __init__(self, policy: ConfirmationPolicy = ConfirmationPolicy.DANGEROUS_ONLY) -> None:
        self._policy = policy

    def set_policy(self, policy: ConfirmationPolicy) -> None:
        """Set confirmation policy."""
        self._policy = policy

    def evaluate_confirmation(
        self,
        request: SecurityRequest,
        risk: RiskAssessment,
        perm: PermissionResult,
    ) -> Optional[ConfirmationRequest]:
        """Determine if user confirmation is required for a request."""
        requires_conf = False

        if self._policy == ConfirmationPolicy.ALWAYS:
            requires_conf = True
        elif self._policy == ConfirmationPolicy.NEVER:
            requires_conf = False
        elif self._policy == ConfirmationPolicy.DANGEROUS_ONLY:
            requires_conf = risk.is_dangerous or risk.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        elif self._policy == ConfirmationPolicy.DESTRUCTIVE_ONLY:
            requires_conf = risk.is_destructive
        elif self._policy == ConfirmationPolicy.ADMIN_ONLY:
            requires_conf = perm.is_admin_required

        if not requires_conf:
            return None

        conf_id = f"conf_{uuid.uuid4().hex[:8]}"
        msg = f"User confirmation required for {request.operation} on '{request.target_resource}' (Risk: {risk.risk_level.value.upper()})"

        return ConfirmationRequest(
            confirmation_id=conf_id,
            request_id=request.request_id,
            prompt_message=msg,
            policy=self._policy,
            risk_level=risk.risk_level,
            timestamp=datetime.now(timezone.utc),
        )
