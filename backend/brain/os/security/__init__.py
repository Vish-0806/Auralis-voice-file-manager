"""Security Subsystem for Auralis Operating System Abstraction (Phase 11.8).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.security.audit_logger import AuditLogger
from brain.os.security.confirmation_manager import ConfirmationManager
from brain.os.security.exceptions import (
    ConfirmationRequiredError,
    PermissionDeniedError,
    PolicyViolationError,
    SecurityException,
    SecurityRiskError,
)
from brain.os.security.interfaces import (
    IAuditLogger,
    IConfirmationManager,
    IPermissionManager,
    IPolicyEngine,
    IRiskAnalyzer,
    ISecurityProvider,
    ISecurityRuntime,
)
from brain.os.security.permission_manager import PermissionManager
from brain.os.security.policy_engine import PolicyEngine
from brain.os.security.risk_analyzer import RiskAnalyzer
from brain.os.security.runtime import get_security_runtime, reset_security_runtime
from brain.os.security.security_models import (
    AuditEvent,
    AuditSeverity,
    ConfirmationPolicy,
    ConfirmationRequest,
    OperationCategory,
    PermissionLevel,
    PermissionResult,
    RiskAssessment,
    RiskLevel,
    SecurityCapabilities,
    SecurityContext,
    SecurityDecision,
    SecurityDecisionType,
    SecurityHealth,
    SecurityRequest,
    SecurityRuntimeStatus,
    SecurityStatistics,
)
from brain.os.security.security_provider import SecurityProvider
from brain.os.security.security_runtime import SecurityRuntime

__all__ = [
    # Enums
    "PermissionLevel",
    "SecurityDecisionType",
    "RiskLevel",
    "ConfirmationPolicy",
    "AuditSeverity",
    "OperationCategory",
    # Models
    "SecurityContext",
    "SecurityRequest",
    "PermissionResult",
    "RiskAssessment",
    "ConfirmationRequest",
    "SecurityDecision",
    "AuditEvent",
    "SecurityCapabilities",
    "SecurityStatistics",
    "SecurityHealth",
    "SecurityRuntimeStatus",
    # Exceptions
    "SecurityException",
    "PermissionDeniedError",
    "PolicyViolationError",
    "SecurityRiskError",
    "ConfirmationRequiredError",
    # Interfaces
    "IPermissionManager",
    "IPolicyEngine",
    "IRiskAnalyzer",
    "IConfirmationManager",
    "IAuditLogger",
    "ISecurityProvider",
    "ISecurityRuntime",
    # Services & Implementations
    "PermissionManager",
    "PolicyEngine",
    "RiskAnalyzer",
    "ConfirmationManager",
    "AuditLogger",
    "SecurityProvider",
    "SecurityRuntime",
    # Singleton Accessors
    "get_security_runtime",
    "reset_security_runtime",
]
