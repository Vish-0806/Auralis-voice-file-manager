"""API Protection & Rate Limiting Runtime Package (Phase 15.8).

Provider-independent Protection Runtime establishing models, exceptions, ABC interfaces,
rate limiter, policy engine, violation tracker, protection provider, runtime coordinator,
and singleton accessors.
"""

from backend.application.api.protection.exceptions import (
    PolicyViolationException,
    ProtectionException,
    QuotaExceededException,
    RateLimitException,
)
from backend.application.api.protection.interfaces import (
    IPolicyEngine,
    IProtectionProvider,
    IProtectionRuntime,
    IRateLimiter,
    IViolationTracker,
)
from backend.application.api.protection.models import (
    ApiPolicy,
    ClientIdentity,
    PolicyDecision,
    ProtectionCapabilities,
    ProtectionContext,
    ProtectionDecision,
    ProtectionDiagnostics,
    ProtectionHealth,
    ProtectionRuntimeState,
    ProtectionStatistics,
    QuotaWindow,
    RateLimitAlgorithm,
    RateLimitDecision,
    RateLimitRule,
    TokenBucket,
    ViolationRecord,
)
from backend.application.api.protection.policy_engine import PolicyEngine
from backend.application.api.protection.protection_provider import (
    ProtectionProvider,
)
from backend.application.api.protection.protection_runtime import (
    ProtectionRuntime,
)
from backend.application.api.protection.rate_limiter import RateLimiter
from backend.application.api.protection.runtime import (
    get_protection_provider,
    get_protection_runtime,
    reset_protection_provider,
    reset_protection_runtime,
    set_protection_provider,
    set_protection_runtime,
)
from backend.application.api.protection.violation_tracker import ViolationTracker

__all__ = [
    # Models & Enums
    "RateLimitAlgorithm",
    "ProtectionDecision",
    "ProtectionRuntimeState",
    "ClientIdentity",
    "RateLimitRule",
    "QuotaWindow",
    "TokenBucket",
    "RateLimitDecision",
    "ApiPolicy",
    "PolicyDecision",
    "ViolationRecord",
    "ProtectionContext",
    "ProtectionCapabilities",
    "ProtectionStatistics",
    "ProtectionHealth",
    "ProtectionDiagnostics",
    # Exceptions
    "ProtectionException",
    "RateLimitException",
    "PolicyViolationException",
    "QuotaExceededException",
    # Interfaces
    "IRateLimiter",
    "IPolicyEngine",
    "IViolationTracker",
    "IProtectionProvider",
    "IProtectionRuntime",
    # Implementations
    "RateLimiter",
    "PolicyEngine",
    "ViolationTracker",
    "ProtectionProvider",
    "ProtectionRuntime",
    # Runtime Helpers
    "get_protection_runtime",
    "set_protection_runtime",
    "reset_protection_runtime",
    "get_protection_provider",
    "set_protection_provider",
    "reset_protection_provider",
]
