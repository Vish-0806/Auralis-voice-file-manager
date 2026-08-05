"""Tests for API Authentication & Authorization Runtime (Phase 15.4).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
identity manager, session manager, authorization manager engine, provider lifecycle,
runtime coordinator, lazy singletons, and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from backend.application.api.auth import (
    AuthenticationCapabilities,
    AuthenticationContext,
    AuthenticationDiagnostics,
    AuthenticationException,
    AuthenticationFailureException,
    AuthenticationHealth,
    AuthenticationProvider,
    AuthenticationRuntime,
    AuthenticationRuntimeState,
    AuthenticationSession,
    AuthenticationState,
    AuthenticationStatistics,
    AuthorizationDecision,
    AuthorizationException,
    AuthorizationManager,
    AuthorizationResult,
    Claim,
    IAuthenticationProvider,
    IAuthenticationRuntime,
    IAuthorizationManager,
    IIdentityManager,
    ISessionManager,
    Identity,
    IdentityException,
    IdentityManager,
    Permission,
    Principal,
    Role,
    SessionException,
    SessionManager,
    get_authentication_provider,
    get_authentication_runtime,
    reset_authentication_provider,
    reset_authentication_runtime,
    set_authentication_provider,
    set_authentication_runtime,
)


@pytest.fixture(autouse=True)
def _reset_auth_singletons():
    """Reset authentication singletons before and after each test."""
    reset_authentication_runtime()
    reset_authentication_provider()
    yield
    reset_authentication_runtime()
    reset_authentication_provider()


# --- Enum Tests ---

def test_enum_authentication_state():
    """Verify AuthenticationState enum values."""
    assert AuthenticationState.UNAUTHENTICATED.value == "UNAUTHENTICATED"
    assert AuthenticationState.AUTHENTICATED.value == "AUTHENTICATED"
    assert AuthenticationState.EXPIRED.value == "EXPIRED"
    assert AuthenticationState.REVOKED.value == "REVOKED"
    assert len(AuthenticationState) == 4


def test_enum_authorization_result():
    """Verify AuthorizationResult enum values."""
    assert AuthorizationResult.GRANTED.value == "GRANTED"
    assert AuthorizationResult.DENIED.value == "DENIED"
    assert AuthorizationResult.NOT_APPLICABLE.value == "NOT_APPLICABLE"
    assert len(AuthorizationResult) == 3


def test_enum_authentication_runtime_state():
    """Verify AuthenticationRuntimeState enum values."""
    assert AuthenticationRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert AuthenticationRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert AuthenticationRuntimeState.READY.value == "READY"
    assert AuthenticationRuntimeState.STOPPING.value == "STOPPING"
    assert AuthenticationRuntimeState.STOPPED.value == "STOPPED"
    assert len(AuthenticationRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_claim():
    """Verify Claim defaults and immutability."""
    c = Claim(key="department", value="engineering")
    assert c.key == "department"
    assert c.issuer == "local"

    with pytest.raises(ValidationError):
        c.value = "sales"  # type: ignore[attr-defined]


def test_model_immutability_permission():
    """Verify Permission defaults and immutability."""
    p = Permission(permission_id="p1", name="ReadFiles", resource="files", action="read")
    assert p.permission_id == "p1"
    assert p.action == "read"

    with pytest.raises(ValidationError):
        p.action = "write"  # type: ignore[attr-defined]


def test_model_immutability_role():
    """Verify Role defaults and immutability."""
    r = Role(role_id="r1", name="Admin")
    assert r.role_id == "r1"
    assert r.name == "Admin"

    with pytest.raises(ValidationError):
        r.name = "User"  # type: ignore[attr-defined]


def test_model_immutability_identity():
    """Verify Identity defaults and immutability."""
    ident = Identity(identity_id="usr_1", username="alice")
    assert ident.identity_id == "usr_1"
    assert ident.is_active is True

    with pytest.raises(ValidationError):
        ident.username = "bob"  # type: ignore[attr-defined]


def test_model_immutability_principal():
    """Verify Principal defaults and immutability."""
    ident = Identity(identity_id="usr_1", username="alice")
    prin = Principal(principal_id="p_1", identity=ident)
    assert prin.principal_id == "p_1"

    with pytest.raises(ValidationError):
        prin.principal_id = "p_2"  # type: ignore[attr-defined]


def test_model_immutability_session():
    """Verify AuthenticationSession defaults and immutability."""
    sess = AuthenticationSession(session_id="s1", identity_id="usr_1")
    assert sess.session_id == "s1"
    assert sess.state == AuthenticationState.AUTHENTICATED

    with pytest.raises(ValidationError):
        sess.state = AuthenticationState.REVOKED  # type: ignore[attr-defined]


def test_model_immutability_authorization_decision():
    """Verify AuthorizationDecision defaults and immutability."""
    dec = AuthorizationDecision(result=AuthorizationResult.GRANTED, identity_id="usr_1")
    assert dec.result == AuthorizationResult.GRANTED

    with pytest.raises(ValidationError):
        dec.result = AuthorizationResult.DENIED  # type: ignore[attr-defined]


def test_model_immutability_authentication_context():
    """Verify AuthenticationContext defaults and immutability."""
    ctx = AuthenticationContext(context_id="c1", is_authenticated=True)
    assert ctx.is_authenticated is True

    with pytest.raises(ValidationError):
        ctx.is_authenticated = False  # type: ignore[attr-defined]


def test_model_immutability_capabilities():
    """Verify AuthenticationCapabilities defaults and immutability."""
    caps = AuthenticationCapabilities()
    assert caps.supports_identity_management is True

    with pytest.raises(ValidationError):
        caps.supports_identity_management = False  # type: ignore[attr-defined]


def test_model_immutability_statistics():
    """Verify AuthenticationStatistics defaults and immutability."""
    stats = AuthenticationStatistics()
    assert stats.total_identities == 0

    with pytest.raises(ValidationError):
        stats.total_identities = 10  # type: ignore[attr-defined]


def test_model_immutability_health():
    """Verify AuthenticationHealth defaults and immutability."""
    health = AuthenticationHealth()
    assert health.is_healthy is True

    with pytest.raises(ValidationError):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_diagnostics():
    """Verify AuthenticationDiagnostics defaults and immutability."""
    diag = AuthenticationDiagnostics()
    assert diag.identities_count == 0

    with pytest.raises(ValidationError):
        diag.identities_count = 5  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify exception hierarchy inheritance."""
    assert issubclass(IdentityException, AuthenticationException)
    assert issubclass(AuthenticationFailureException, AuthenticationException)
    assert issubclass(AuthorizationException, AuthenticationException)
    assert issubclass(SessionException, AuthenticationException)
    assert issubclass(AuthenticationException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on direct instantiation."""
    with pytest.raises(TypeError):
        IIdentityManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        ISessionManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IAuthorizationManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IAuthenticationProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IAuthenticationRuntime()  # type: ignore[abstract]


# --- IdentityManager Tests ---

def test_identity_manager_register_and_lookup():
    """Verify identity registration and lookup."""
    mgr = IdentityManager()
    ident = Identity(identity_id="usr_1", username="alice")
    registered = mgr.register_identity(ident)

    assert registered.identity_id == "usr_1"
    assert mgr.lookup_identity("usr_1") == ident
    assert mgr.count_identities() == 1


def test_identity_manager_duplicate_identity_exception():
    """Verify IdentityException on duplicate identity registration."""
    mgr = IdentityManager()
    ident1 = Identity(identity_id="usr_1", username="alice")
    ident2 = Identity(identity_id="usr_1", username="bob")

    mgr.register_identity(ident1)
    with pytest.raises(IdentityException):
        mgr.register_identity(ident2)


def test_identity_manager_principal_auto_creation():
    """Verify automatic Principal creation on identity registration."""
    mgr = IdentityManager()
    role = Role(role_id="r1", name="Admin")
    ident = Identity(identity_id="usr_1", username="alice", roles=(role,))
    mgr.register_identity(ident)

    prin = mgr.lookup_principal("principal_usr_1")
    assert prin is not None
    assert prin.principal_id == "principal_usr_1"
    assert prin.identity.identity_id == "usr_1"
    assert "Admin" in prin.active_roles


def test_identity_manager_assign_role():
    """Verify assigning a role to an existing identity."""
    mgr = IdentityManager()
    ident = Identity(identity_id="usr_1", username="alice")
    mgr.register_identity(ident)

    role = Role(role_id="r1", name="Editor")
    updated = mgr.assign_role("usr_1", role)

    assert updated is not None
    assert len(updated.roles) == 1
    assert updated.roles[0].name == "Editor"


def test_identity_manager_add_claim():
    """Verify adding a claim to an existing identity."""
    mgr = IdentityManager()
    ident = Identity(identity_id="usr_1", username="alice")
    mgr.register_identity(ident)

    claim = Claim(key="tier", value="premium")
    updated = mgr.add_claim("usr_1", claim)

    assert updated is not None
    assert len(updated.claims) == 1
    assert updated.claims[0].key == "tier"


def test_identity_manager_list_and_count():
    """Verify list_identities and count_identities."""
    mgr = IdentityManager()
    mgr.register_identity(Identity(identity_id="u1", username="alice"))
    mgr.register_identity(Identity(identity_id="u2", username="bob"))

    assert mgr.count_identities() == 2
    assert len(mgr.list_identities()) == 2


# --- SessionManager Tests ---

def test_session_manager_create_session():
    """Verify session creation."""
    mgr = SessionManager()
    sess = mgr.create_session(identity_id="usr_1", ttl_seconds=3600.0)

    assert sess.identity_id == "usr_1"
    assert sess.state == AuthenticationState.AUTHENTICATED
    assert sess.expires_at is not None


def test_session_manager_get_session():
    """Verify retrieving a session by ID."""
    mgr = SessionManager()
    sess = mgr.create_session(identity_id="usr_1")
    retrieved = mgr.get_session(sess.session_id)

    assert retrieved is not None
    assert retrieved.session_id == sess.session_id


def test_session_manager_automatic_expiration():
    """Verify automatic session expiration when ttl has elapsed."""
    mgr = SessionManager()

    # Manually insert an expired session
    now = datetime.now(timezone.utc)
    expired_sess = AuthenticationSession(
        session_id="s_exp",
        identity_id="usr_1",
        state=AuthenticationState.AUTHENTICATED,
        created_at=now - timedelta(seconds=7200),
        expires_at=now - timedelta(seconds=3600),
    )
    mgr._sessions["s_exp"] = expired_sess

    checked = mgr.get_session("s_exp")
    assert checked is not None
    assert checked.state == AuthenticationState.EXPIRED


def test_session_manager_revoke_session():
    """Verify session revocation."""
    mgr = SessionManager()
    sess = mgr.create_session(identity_id="usr_1")
    revoked = mgr.revoke_session(sess.session_id)

    assert revoked is not None
    assert revoked.state == AuthenticationState.REVOKED


def test_session_manager_explicit_expire_session():
    """Verify explicit session expiration."""
    mgr = SessionManager()
    sess = mgr.create_session(identity_id="usr_1")
    expired = mgr.expire_session(sess.session_id)

    assert expired is not None
    assert expired.state == AuthenticationState.EXPIRED


def test_session_manager_list_active_sessions():
    """Verify listing active sessions excluding revoked/expired ones."""
    mgr = SessionManager()
    s1 = mgr.create_session(identity_id="u1")
    s2 = mgr.create_session(identity_id="u2")
    mgr.revoke_session(s2.session_id)

    active = mgr.list_active_sessions()
    assert len(active) == 1
    assert active[0].session_id == s1.session_id


# --- AuthorizationManager Tests ---

def test_authorization_manager_permission_granted():
    """Verify permission evaluation GRANTED."""
    mgr = AuthorizationManager()
    perm = Permission(permission_id="p1", name="ReadFiles", resource="files", action="read")
    role = Role(role_id="r1", name="Reader", permissions=(perm,))
    ident = Identity(identity_id="u1", username="alice", roles=(role,))

    decision = mgr.evaluate(ident, resource="files", action="read")
    assert decision.result == AuthorizationResult.GRANTED
    assert decision.identity_id == "u1"


def test_authorization_manager_permission_wildcard():
    """Verify permission evaluation GRANTED via wildcard resource/action."""
    mgr = AuthorizationManager()
    perm = Permission(permission_id="p1", name="AdminAll", resource="*", action="*")
    role = Role(role_id="r1", name="Admin", permissions=(perm,))
    ident = Identity(identity_id="u1", username="alice", roles=(role,))

    decision = mgr.evaluate(ident, resource="settings", action="delete")
    assert decision.result == AuthorizationResult.GRANTED


def test_authorization_manager_permission_denied():
    """Verify permission evaluation DENIED when no permission matches."""
    mgr = AuthorizationManager()
    perm = Permission(permission_id="p1", name="ReadFiles", resource="files", action="read")
    role = Role(role_id="r1", name="Reader", permissions=(perm,))
    ident = Identity(identity_id="u1", username="alice", roles=(role,))

    decision = mgr.evaluate(ident, resource="files", action="delete")
    assert decision.result == AuthorizationResult.DENIED


def test_authorization_manager_evaluate_role_granted():
    """Verify role evaluation GRANTED."""
    mgr = AuthorizationManager()
    role = Role(role_id="r1", name="Manager")
    ident = Identity(identity_id="u1", username="alice", roles=(role,))

    decision = mgr.evaluate_role(ident, "Manager")
    assert decision.result == AuthorizationResult.GRANTED


def test_authorization_manager_evaluate_role_denied():
    """Verify role evaluation DENIED when identity lacks role."""
    mgr = AuthorizationManager()
    ident = Identity(identity_id="u1", username="alice")

    decision = mgr.evaluate_role(ident, "Admin")
    assert decision.result == AuthorizationResult.DENIED


def test_authorization_manager_evaluate_claim_granted():
    """Verify claim evaluation GRANTED."""
    mgr = AuthorizationManager()
    claim = Claim(key="tier", value="gold")
    ident = Identity(identity_id="u1", username="alice", claims=(claim,))

    decision = mgr.evaluate_claim(ident, claim_key="tier", claim_value="gold")
    assert decision.result == AuthorizationResult.GRANTED


def test_authorization_manager_evaluate_claim_denied():
    """Verify claim evaluation DENIED when claim value mismatch."""
    mgr = AuthorizationManager()
    claim = Claim(key="tier", value="silver")
    ident = Identity(identity_id="u1", username="alice", claims=(claim,))

    decision = mgr.evaluate_claim(ident, claim_key="tier", claim_value="gold")
    assert decision.result == AuthorizationResult.DENIED


def test_authorization_manager_inactive_identity_denied():
    """Verify inactive identity evaluations are always DENIED."""
    mgr = AuthorizationManager()
    perm = Permission(permission_id="p1", name="All", resource="*", action="*")
    role = Role(role_id="r1", name="Admin", permissions=(perm,))
    ident = Identity(identity_id="u1", username="alice", is_active=False, roles=(role,))

    decision = mgr.evaluate(ident, resource="files", action="read")
    assert decision.result == AuthorizationResult.DENIED


# --- Provider & Runtime Lifecycle Tests ---

def test_provider_lifecycle():
    """Verify AuthenticationProvider initialize and shutdown transitions."""
    provider = AuthenticationProvider()
    assert provider.health().state == AuthenticationRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == AuthenticationRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == AuthenticationRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify AuthenticationProvider restart cycle."""
    provider = AuthenticationProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == AuthenticationRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health_stats_caps_diag():
    """Verify health, statistics, capabilities, and diagnostics from provider."""
    id_mgr = IdentityManager()
    id_mgr.register_identity(Identity(identity_id="u1", username="alice"))

    provider = AuthenticationProvider(identity_manager=id_mgr)
    provider.initialize()

    assert provider.health().is_healthy is True
    assert provider.statistics().total_identities == 1
    assert provider.capabilities().supports_role_based_access is True
    assert provider.diagnostics().identities_count == 1


def test_runtime_lifecycle_delegation():
    """Verify AuthenticationRuntime delegates lifecycle calls to provider."""
    runtime = AuthenticationRuntime()
    assert runtime.health().state == AuthenticationRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == AuthenticationRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == AuthenticationRuntimeState.STOPPED


def test_constructor_dependency_injection():
    """Verify Constructor DI in AuthenticationProvider and AuthenticationRuntime."""
    id_mgr = IdentityManager()
    sess_mgr = SessionManager()
    auth_mgr = AuthorizationManager()

    provider = AuthenticationProvider(
        identity_manager=id_mgr,
        session_manager=sess_mgr,
        authorization_manager=auth_mgr,
    )
    runtime = AuthenticationRuntime(provider=provider)

    assert runtime.get_provider().get_identity_manager() is id_mgr
    assert runtime.get_provider().get_session_manager() is sess_mgr
    assert runtime.get_provider().get_authorization_manager() is auth_mgr


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_auth_runtime():
    """Verify get_authentication_runtime, set_authentication_runtime, and reset_authentication_runtime."""
    r1 = get_authentication_runtime()
    r2 = get_authentication_runtime()
    assert r1 is r2
    assert isinstance(r1, AuthenticationRuntime)

    custom = AuthenticationRuntime()
    set_authentication_runtime(custom)
    assert get_authentication_runtime() is custom

    reset_authentication_runtime()
    r3 = get_authentication_runtime()
    assert r3 is not custom


def test_lazy_singleton_auth_provider():
    """Verify get_authentication_provider, set_authentication_provider, and reset_authentication_provider."""
    p1 = get_authentication_provider()
    p2 = get_authentication_provider()
    assert p1 is p2
    assert isinstance(p1, AuthenticationProvider)

    custom = AuthenticationProvider()
    set_authentication_provider(custom)
    assert get_authentication_provider() is custom

    reset_authentication_provider()
    p3 = get_authentication_provider()
    assert p3 is not custom


# --- Concurrency Tests ---

def test_concurrent_identity_manager_operations():
    """Verify thread-safety of IdentityManager under concurrent identity registrations."""
    mgr = IdentityManager()

    def register_worker(idx: int):
        mgr.register_identity(Identity(identity_id=f"u_{idx}", username=f"user_{idx}"))

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_worker, i) for i in range(40)]
        for f in futures:
            f.result()

    assert mgr.count_identities() == 40


def test_concurrent_session_manager_operations():
    """Verify thread-safety of SessionManager under concurrent session creation."""
    mgr = SessionManager()

    def session_worker(idx: int):
        return mgr.create_session(identity_id=f"u_{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(session_worker, i) for i in range(50)]
        sessions = [f.result() for f in futures]

    assert len(sessions) == 50
    assert mgr.count_sessions() == 50


def test_concurrent_authorization_evaluations():
    """Verify thread-safety of AuthorizationManager under concurrent evaluations."""
    mgr = AuthorizationManager()
    perm = Permission(permission_id="p1", name="Read", resource="files", action="read")
    role = Role(role_id="r1", name="Reader", permissions=(perm,))
    ident = Identity(identity_id="u1", username="alice", roles=(role,))

    def eval_worker(idx: int):
        return mgr.evaluate(ident, resource="files", action="read")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(eval_worker, i) for i in range(50)]
        decisions = [f.result() for f in futures]

    assert len(decisions) == 50
    assert all(d.result == AuthorizationResult.GRANTED for d in decisions)
