"""API Authentication & Authorization Runtime Package (Phase 15.4).

Provider-independent Authentication & Authorization Runtime establishing models,
exceptions, ABC interfaces, identity manager, session manager, authorization manager,
authentication provider, runtime coordinator, and singleton accessors.
"""

from backend.application.api.auth.authentication_provider import (
    AuthenticationProvider,
)
from backend.application.api.auth.authentication_runtime import (
    AuthenticationRuntime,
)
from backend.application.api.auth.authorization_manager import (
    AuthorizationManager,
)
from backend.application.api.auth.exceptions import (
    AuthenticationException,
    AuthenticationFailureException,
    AuthorizationException,
    IdentityException,
    SessionException,
)
from backend.application.api.auth.identity_manager import IdentityManager
from backend.application.api.auth.interfaces import (
    IAuthenticationProvider,
    IAuthenticationRuntime,
    IAuthorizationManager,
    IIdentityManager,
    ISessionManager,
)
from backend.application.api.auth.models import (
    AuthenticationCapabilities,
    AuthenticationContext,
    AuthenticationDiagnostics,
    AuthenticationHealth,
    AuthenticationRuntimeState,
    AuthenticationSession,
    AuthenticationState,
    AuthenticationStatistics,
    AuthorizationDecision,
    AuthorizationResult,
    Claim,
    Identity,
    Permission,
    Principal,
    Role,
)
from backend.application.api.auth.runtime import (
    get_authentication_provider,
    get_authentication_runtime,
    reset_authentication_provider,
    reset_authentication_runtime,
    set_authentication_provider,
    set_authentication_runtime,
)
from backend.application.api.auth.session_manager import SessionManager

__all__ = [
    # Models & Enums
    "AuthenticationState",
    "AuthorizationResult",
    "AuthenticationRuntimeState",
    "Claim",
    "Permission",
    "Role",
    "Identity",
    "Principal",
    "AuthenticationSession",
    "AuthorizationDecision",
    "AuthenticationContext",
    "AuthenticationCapabilities",
    "AuthenticationStatistics",
    "AuthenticationHealth",
    "AuthenticationDiagnostics",
    # Exceptions
    "AuthenticationException",
    "IdentityException",
    "AuthenticationFailureException",
    "AuthorizationException",
    "SessionException",
    # Interfaces
    "IIdentityManager",
    "ISessionManager",
    "IAuthorizationManager",
    "IAuthenticationProvider",
    "IAuthenticationRuntime",
    # Implementations
    "IdentityManager",
    "SessionManager",
    "AuthorizationManager",
    "AuthenticationProvider",
    "AuthenticationRuntime",
    # Runtime Helpers
    "get_authentication_runtime",
    "set_authentication_runtime",
    "reset_authentication_runtime",
    "get_authentication_provider",
    "set_authentication_provider",
    "reset_authentication_provider",
]
