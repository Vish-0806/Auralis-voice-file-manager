"""Abstract interfaces for Security Subsystem (Phase 11.8).

Defines canonical interfaces for Permission Manager, Policy Engine, Risk Analyzer,
Confirmation Manager, Audit Logger, Security Provider, and Security Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.os.security.security_models import (
    AuditEvent,
    ConfirmationRequest,
    OperationCategory,
    PermissionResult,
    RiskAssessment,
    SecurityCapabilities,
    SecurityDecision,
    SecurityDecisionType,
    SecurityHealth,
    SecurityRequest,
    SecurityRuntimeStatus,
    SecurityStatistics,
)


class IPermissionManager(ABC):
    """Interface for permission validation and admin privilege detection."""

    @abstractmethod
    def validate_permission(self, request: SecurityRequest) -> PermissionResult:
        """Validate permissions required for a security request."""
        pass


class IPolicyEngine(ABC):
    """Interface for evaluating configurable execution security policies."""

    @abstractmethod
    def evaluate_policy(
        self, request: SecurityRequest, perm_result: PermissionResult
    ) -> SecurityDecisionType:
        """Evaluate execution policy decision for a request."""
        pass

    @abstractmethod
    def set_policy(
        self, category: OperationCategory, decision: SecurityDecisionType
    ) -> None:
        """Configure default policy decision for an operation category."""
        pass


class IRiskAnalyzer(ABC):
    """Interface for analyzing operation parameters and rating risk level."""

    @abstractmethod
    def analyze_risk(self, request: SecurityRequest) -> RiskAssessment:
        """Perform risk assessment and factor classification for a request."""
        pass


class IConfirmationManager(ABC):
    """Interface for evaluating user confirmation enforcement policies."""

    @abstractmethod
    def evaluate_confirmation(
        self,
        request: SecurityRequest,
        risk: RiskAssessment,
        perm: PermissionResult,
    ) -> Optional[ConfirmationRequest]:
        """Determine if user confirmation is required for a request."""
        pass


class IAuditLogger(ABC):
    """Interface for recording thread-safe security decision audit logs."""

    @abstractmethod
    def log_decision(
        self, request: SecurityRequest, decision: SecurityDecision
    ) -> AuditEvent:
        """Record a security decision event in the audit trail."""
        pass

    @abstractmethod
    def get_audit_history(
        self, category: Optional[OperationCategory] = None
    ) -> List[AuditEvent]:
        """Retrieve recorded audit trail events."""
        pass

    @abstractmethod
    def clear_audit_history(self) -> None:
        """Clear audit history log."""
        pass


class ISecurityProvider(ABC):
    """Interface for Security Subsystem Provider."""

    @abstractmethod
    def get_permission_manager(self) -> IPermissionManager:
        """Return permission manager."""
        pass

    @abstractmethod
    def get_policy_engine(self) -> IPolicyEngine:
        """Return policy engine."""
        pass

    @abstractmethod
    def get_risk_analyzer(self) -> IRiskAnalyzer:
        """Return risk analyzer."""
        pass

    @abstractmethod
    def get_confirmation_manager(self) -> IConfirmationManager:
        """Return confirmation manager."""
        pass

    @abstractmethod
    def get_audit_logger(self) -> IAuditLogger:
        """Return audit logger."""
        pass

    @abstractmethod
    def evaluate_request(self, request: SecurityRequest) -> SecurityDecision:
        """Evaluate a security decision request through the security pipeline."""
        pass

    @abstractmethod
    def get_health(self) -> SecurityHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> SecurityStatistics:
        """Return security statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> SecurityCapabilities:
        """Return security capabilities."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        pass


class ISecurityRuntime(ABC):
    """Interface for Security Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize security runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown security runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: ISecurityProvider) -> None:
        """Register security provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[ISecurityProvider]:
        """Get registered security provider."""
        pass

    @abstractmethod
    def evaluate_request(self, request: SecurityRequest) -> SecurityDecision:
        """Evaluate a security decision request."""
        pass

    @abstractmethod
    def get_statistics(self) -> SecurityStatistics:
        """Get security runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> SecurityRuntimeStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        pass
