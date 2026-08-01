"""Security Provider implementation (Phase 11.8).

Aggregates PermissionManager, PolicyEngine, RiskAnalyzer, ConfirmationManager, and AuditLogger
into a unified security gateway provider.
"""

from datetime import datetime, timezone
import time
import uuid
from typing import Any, Dict, Optional

from brain.os.security.audit_logger import AuditLogger
from brain.os.security.confirmation_manager import ConfirmationManager
from brain.os.security.interfaces import (
    IAuditLogger,
    IConfirmationManager,
    IPermissionManager,
    IPolicyEngine,
    IRiskAnalyzer,
    ISecurityProvider,
)
from brain.os.security.permission_manager import PermissionManager
from brain.os.security.policy_engine import PolicyEngine
from brain.os.security.risk_analyzer import RiskAnalyzer
from brain.os.security.security_models import (
    SecurityCapabilities,
    SecurityDecision,
    SecurityDecisionType,
    SecurityHealth,
    SecurityRequest,
    SecurityStatistics,
)


class SecurityProvider(ISecurityProvider):
    """Canonical security subsystem provider."""

    def __init__(
        self,
        permission_manager: Optional[IPermissionManager] = None,
        policy_engine: Optional[IPolicyEngine] = None,
        risk_analyzer: Optional[IRiskAnalyzer] = None,
        confirmation_manager: Optional[IConfirmationManager] = None,
        audit_logger: Optional[IAuditLogger] = None,
    ) -> None:
        self._permission_manager = permission_manager or PermissionManager()
        self._policy_engine = policy_engine or PolicyEngine()
        self._risk_analyzer = risk_analyzer or RiskAnalyzer()
        self._confirmation_manager = confirmation_manager or ConfirmationManager()
        self._audit_logger = audit_logger or AuditLogger()

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

        self._total_evaluated = 0
        self._allowed_count = 0
        self._denied_count = 0
        self._confirmation_count = 0

    def get_permission_manager(self) -> IPermissionManager:
        """Return permission manager."""
        return self._permission_manager

    def get_policy_engine(self) -> IPolicyEngine:
        """Return policy engine."""
        return self._policy_engine

    def get_risk_analyzer(self) -> IRiskAnalyzer:
        """Return risk analyzer."""
        return self._risk_analyzer

    def get_confirmation_manager(self) -> IConfirmationManager:
        """Return confirmation manager."""
        return self._confirmation_manager

    def get_audit_logger(self) -> IAuditLogger:
        """Return audit logger."""
        return self._audit_logger

    def evaluate_request(self, request: SecurityRequest) -> SecurityDecision:
        """Evaluate a security decision request through the security pipeline."""
        if not request.request_id:
            req_id = f"req_{uuid.uuid4().hex[:8]}"
            request = SecurityRequest(
                request_id=req_id,
                category=request.category,
                operation=request.operation,
                target_resource=request.target_resource,
                requested_permission=request.requested_permission,
                context=request.context,
                parameters=request.parameters,
            )

        perm_res = self._permission_manager.validate_permission(request)
        risk = self._risk_analyzer.analyze_risk(request)
        decision_type = self._policy_engine.evaluate_policy(request, perm_res)

        conf_req = None
        if decision_type != SecurityDecisionType.DENY:
            conf_req = self._confirmation_manager.evaluate_confirmation(request, risk, perm_res)
            if conf_req is not None:
                decision_type = SecurityDecisionType.REQUIRE_CONFIRMATION

        reason = perm_res.reason
        if decision_type == SecurityDecisionType.DENY:
            reason = f"Operation denied: {perm_res.reason}"
        elif decision_type == SecurityDecisionType.REQUIRE_CONFIRMATION:
            reason = "User confirmation required before execution"

        decision = SecurityDecision(
            request_id=request.request_id,
            decision_type=decision_type,
            permission_result=perm_res,
            risk_assessment=risk,
            confirmation_request=conf_req,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
        )

        self._audit_logger.log_decision(request, decision)

        self._total_evaluated += 1
        if decision_type == SecurityDecisionType.ALLOW:
            self._allowed_count += 1
        elif decision_type == SecurityDecisionType.DENY:
            self._denied_count += 1
        elif decision_type == SecurityDecisionType.REQUIRE_CONFIRMATION:
            self._confirmation_count += 1

        return decision

    def get_health(self) -> SecurityHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        audit_size = len(self._audit_logger.get_audit_history())

        return SecurityHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            audit_log_size=audit_size,
            total_evaluations=self._total_evaluated,
            uptime_seconds=uptime,
            details={"provider_type": "SecurityProvider"},
        )

    def get_statistics(self) -> SecurityStatistics:
        """Return security statistics."""
        audit_size = len(self._audit_logger.get_audit_history())
        return SecurityStatistics(
            total_requests_evaluated=self._total_evaluated,
            allowed_requests=self._allowed_count,
            denied_requests=self._denied_count,
            confirmation_requests=self._confirmation_count,
            audit_events_count=audit_size,
        )

    def get_capabilities(self) -> SecurityCapabilities:
        """Return security capabilities."""
        return SecurityCapabilities(
            supports_risk_analysis=True,
            supports_audit_logging=True,
            supports_policy_evaluation=True,
            supports_confirmation=True,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        health = self.get_health()
        stats = self.get_statistics()

        return {
            "provider_type": "SecurityProvider",
            "healthy": health.healthy,
            "total_evaluated": stats.total_requests_evaluated,
            "allowed_requests": stats.allowed_requests,
            "denied_requests": stats.denied_requests,
            "confirmation_requests": stats.confirmation_requests,
            "audit_events_count": stats.audit_events_count,
            "uptime_seconds": health.uptime_seconds,
            "created_at": self._created_at.isoformat(),
        }
