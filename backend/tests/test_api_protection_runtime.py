"""Tests for API Protection & Rate Limiting Runtime (Phase 15.8).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
rate limiter algorithms (sliding window, token bucket), policy engine priority evaluation,
violation tracker cooldowns, provider lifecycle, runtime coordinator, lazy singletons,
and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import time
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError as PydanticValidationError

from backend.application.api.protection import (
    ApiPolicy,
    ClientIdentity,
    IPolicyEngine,
    IProtectionProvider,
    IProtectionRuntime,
    IRateLimiter,
    IViolationTracker,
    PolicyDecision,
    PolicyEngine,
    PolicyViolationException,
    ProtectionCapabilities,
    ProtectionContext,
    ProtectionDecision,
    ProtectionDiagnostics,
    ProtectionException,
    ProtectionHealth,
    ProtectionProvider,
    ProtectionRuntime,
    ProtectionRuntimeState,
    ProtectionStatistics,
    QuotaExceededException,
    QuotaWindow,
    RateLimitAlgorithm,
    RateLimitDecision,
    RateLimitException,
    RateLimiter,
    RateLimitRule,
    TokenBucket,
    ViolationRecord,
    ViolationTracker,
    get_protection_provider,
    get_protection_runtime,
    reset_protection_provider,
    reset_protection_runtime,
    set_protection_provider,
    set_protection_runtime,
)


@pytest.fixture(autouse=True)
def _reset_protection_singletons():
    """Reset protection singletons before and after each test."""
    reset_protection_runtime()
    reset_protection_provider()
    yield
    reset_protection_runtime()
    reset_protection_provider()


# --- Enum Tests ---

def test_enum_rate_limit_algorithm():
    """Verify RateLimitAlgorithm enum values."""
    assert RateLimitAlgorithm.FIXED_WINDOW.value == "FIXED_WINDOW"
    assert RateLimitAlgorithm.SLIDING_WINDOW.value == "SLIDING_WINDOW"
    assert RateLimitAlgorithm.TOKEN_BUCKET.value == "TOKEN_BUCKET"
    assert RateLimitAlgorithm.LEAKY_BUCKET.value == "LEAKY_BUCKET"
    assert len(RateLimitAlgorithm) == 4


def test_enum_protection_decision():
    """Verify ProtectionDecision enum values."""
    assert ProtectionDecision.ALLOW.value == "ALLOW"
    assert ProtectionDecision.THROTTLE.value == "THROTTLE"
    assert ProtectionDecision.REJECT.value == "REJECT"
    assert len(ProtectionDecision) == 3


def test_enum_protection_runtime_state():
    """Verify ProtectionRuntimeState enum values."""
    assert ProtectionRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ProtectionRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert ProtectionRuntimeState.READY.value == "READY"
    assert ProtectionRuntimeState.STOPPING.value == "STOPPING"
    assert ProtectionRuntimeState.STOPPED.value == "STOPPED"
    assert len(ProtectionRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_client_identity():
    """Verify ClientIdentity defaults and immutability."""
    client = ClientIdentity(client_id="c1", client_ip="127.0.0.1")
    assert client.client_id == "c1"

    with pytest.raises((PydanticValidationError, TypeError)):
        client.client_id = "c2"  # type: ignore[attr-defined]


def test_model_immutability_rate_limit_rule():
    """Verify RateLimitRule defaults and immutability."""
    rule = RateLimitRule(rule_id="r1", name="Rule1", max_requests=10)
    assert rule.rule_id == "r1"
    assert rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW

    with pytest.raises((PydanticValidationError, TypeError)):
        rule.max_requests = 100  # type: ignore[attr-defined]


def test_model_immutability_quota_window():
    """Verify QuotaWindow defaults and immutability."""
    window = QuotaWindow(window_id="w1", client_id="c1", rule_id="r1")
    assert window.window_id == "w1"

    with pytest.raises((PydanticValidationError, TypeError)):
        window.current_count = 5  # type: ignore[attr-defined]


def test_model_immutability_token_bucket():
    """Verify TokenBucket defaults and immutability."""
    bucket = TokenBucket(bucket_id="tb1", client_id="c1", capacity=10, current_tokens=10.0, refill_rate=1.0)
    assert bucket.bucket_id == "tb1"

    with pytest.raises((PydanticValidationError, TypeError)):
        bucket.current_tokens = 5.0  # type: ignore[attr-defined]


def test_model_immutability_rate_limit_decision():
    """Verify RateLimitDecision defaults and immutability."""
    dec = RateLimitDecision(decision_id="d1", is_allowed=True)
    assert dec.decision_id == "d1"

    with pytest.raises((PydanticValidationError, TypeError)):
        dec.is_allowed = False  # type: ignore[attr-defined]


def test_model_immutability_api_policy():
    """Verify ApiPolicy defaults and immutability."""
    pol = ApiPolicy(policy_id="p1", name="DefaultPolicy")
    assert pol.policy_id == "p1"

    with pytest.raises((PydanticValidationError, TypeError)):
        pol.priority = 1  # type: ignore[attr-defined]


def test_model_immutability_policy_decision():
    """Verify PolicyDecision defaults and immutability."""
    pdec = PolicyDecision(decision_id="pd1", client_id="c1")
    assert pdec.decision_id == "pd1"

    with pytest.raises((PydanticValidationError, TypeError)):
        pdec.action = ProtectionDecision.REJECT  # type: ignore[attr-defined]


def test_model_immutability_violation_record():
    """Verify ViolationRecord defaults and immutability."""
    viol = ViolationRecord(violation_id="v1", client_id="c1", rule_id="r1", reason="Exceeded rate limit")
    assert viol.violation_id == "v1"

    with pytest.raises((PydanticValidationError, TypeError)):
        viol.reason = "Other"  # type: ignore[attr-defined]


def test_model_immutability_protection_context():
    """Verify ProtectionContext defaults and immutability."""
    client = ClientIdentity(client_id="c1")
    ctx = ProtectionContext(context_id="ctx1", client=client, path="/api/v1/resource")
    assert ctx.context_id == "ctx1"

    with pytest.raises((PydanticValidationError, TypeError)):
        ctx.path = "/new_path"  # type: ignore[attr-defined]


def test_model_immutability_capabilities():
    """Verify ProtectionCapabilities defaults and immutability."""
    caps = ProtectionCapabilities()
    assert caps.supports_rate_limiting is True

    with pytest.raises((PydanticValidationError, TypeError)):
        caps.supports_rate_limiting = False  # type: ignore[attr-defined]


def test_model_immutability_statistics():
    """Verify ProtectionStatistics defaults and immutability."""
    stats = ProtectionStatistics()
    assert stats.total_rules == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        stats.total_rules = 5  # type: ignore[attr-defined]


def test_model_immutability_health():
    """Verify ProtectionHealth defaults and immutability."""
    health = ProtectionHealth()
    assert health.is_healthy is True

    with pytest.raises((PydanticValidationError, TypeError)):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_diagnostics():
    """Verify ProtectionDiagnostics defaults and immutability."""
    diag = ProtectionDiagnostics()
    assert diag.registered_rules_count == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        diag.registered_rules_count = 10  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify exception hierarchy inheritance."""
    assert issubclass(RateLimitException, ProtectionException)
    assert issubclass(PolicyViolationException, ProtectionException)
    assert issubclass(QuotaExceededException, ProtectionException)
    assert issubclass(ProtectionException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on direct instantiation."""
    with pytest.raises(TypeError):
        IRateLimiter()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IPolicyEngine()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IViolationTracker()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IProtectionProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IProtectionRuntime()  # type: ignore[abstract]


# --- RateLimiter Tests ---

def test_rate_limiter_register_and_lookup():
    """Verify registering and looking up a RateLimitRule."""
    limiter = RateLimiter()
    rule = RateLimitRule(rule_id="r1", name="Standard", max_requests=10)
    registered = limiter.register_rule(rule)

    assert registered.rule_id == "r1"
    assert limiter.lookup_rule("r1") == rule
    assert limiter.count_rules() == 1


def test_rate_limiter_duplicate_rule_exception():
    """Verify RateLimitException on duplicate rule ID."""
    limiter = RateLimiter()
    rule1 = RateLimitRule(rule_id="r1", name="R1", max_requests=10)
    rule2 = RateLimitRule(rule_id="r1", name="R2", max_requests=20)

    limiter.register_rule(rule1)
    with pytest.raises(RateLimitException):
        limiter.register_rule(rule2)


def test_rate_limiter_unregister():
    """Verify unregistering a rate limit rule."""
    limiter = RateLimiter()
    rule = RateLimitRule(rule_id="r1", name="R1", max_requests=10)
    limiter.register_rule(rule)

    removed = limiter.unregister_rule("r1")
    assert removed == rule
    assert limiter.lookup_rule("r1") is None
    assert limiter.count_rules() == 0


def test_rate_limiter_sliding_window_allow():
    """Verify sliding window algorithm allows requests within quota."""
    limiter = RateLimiter()
    limiter.register_rule(RateLimitRule(rule_id="r1", name="R1", max_requests=3, window_seconds=60))

    dec1 = limiter.evaluate_rate_limit("client_1", "r1")
    dec2 = limiter.evaluate_rate_limit("client_1", "r1")

    assert dec1.is_allowed is True
    assert dec1.remaining_tokens == 2
    assert dec2.is_allowed is True
    assert dec2.remaining_tokens == 1


def test_rate_limiter_sliding_window_exceeded():
    """Verify sliding window algorithm rejects when max_requests exceeded."""
    limiter = RateLimiter()
    limiter.register_rule(RateLimitRule(rule_id="r1", name="R1", max_requests=2, window_seconds=60))

    limiter.evaluate_rate_limit("client_1", "r1")
    limiter.evaluate_rate_limit("client_1", "r1")
    dec3 = limiter.evaluate_rate_limit("client_1", "r1")

    assert dec3.is_allowed is False
    assert dec3.remaining_tokens == 0
    assert dec3.retry_after_seconds > 0.0


def test_rate_limiter_token_bucket_allow_and_deplete():
    """Verify token bucket algorithm token consumption."""
    limiter = RateLimiter()
    rule = RateLimitRule(
        rule_id="r_tb",
        name="TB",
        max_requests=2,
        window_seconds=60,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        burst_capacity=2,
        refill_rate=0.1,
    )
    limiter.register_rule(rule)

    dec1 = limiter.evaluate_rate_limit("c1", "r_tb")
    dec2 = limiter.evaluate_rate_limit("c1", "r_tb")
    dec3 = limiter.evaluate_rate_limit("c1", "r_tb")

    assert dec1.is_allowed is True
    assert dec2.is_allowed is True
    assert dec3.is_allowed is False


def test_rate_limiter_token_bucket_refill_accounting():
    """Verify token bucket refill accounting over time."""
    limiter = RateLimiter()
    rule = RateLimitRule(
        rule_id="r_tb_refill",
        name="TBRefill",
        max_requests=1,
        window_seconds=1,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        burst_capacity=1,
        refill_rate=100.0,  # Fast refill for testing
    )
    limiter.register_rule(rule)

    dec1 = limiter.evaluate_rate_limit("c1", "r_tb_refill")
    assert dec1.is_allowed is True

    time.sleep(0.02)  # 20ms refill at 100 tokens/sec = 2 tokens refilled
    dec2 = limiter.evaluate_rate_limit("c1", "r_tb_refill")
    assert dec2.is_allowed is True


def test_rate_limiter_unregistered_rule_exception():
    """Verify RateLimitException when evaluating an unregistered rule."""
    limiter = RateLimiter()
    with pytest.raises(RateLimitException):
        limiter.evaluate_rate_limit("c1", "missing_rule")


def test_rate_limiter_list_and_count():
    """Verify list_rules and count_rules."""
    limiter = RateLimiter()
    limiter.register_rule(RateLimitRule(rule_id="r1", name="R1", max_requests=5))
    limiter.register_rule(RateLimitRule(rule_id="r2", name="R2", max_requests=10))

    assert limiter.count_rules() == 2
    assert len(limiter.list_rules()) == 2


def test_rate_limiter_clear():
    """Verify clearing rate limiter."""
    limiter = RateLimiter()
    limiter.register_rule(RateLimitRule(rule_id="r1", name="R1", max_requests=5))
    limiter.clear()

    assert limiter.count_rules() == 0


# --- PolicyEngine Tests ---

def test_policy_engine_register_and_lookup():
    """Verify registering and looking up ApiPolicy."""
    engine = PolicyEngine()
    policy = ApiPolicy(policy_id="p1", name="StrictPolicy")
    registered = engine.register_policy(policy)

    assert registered.policy_id == "p1"
    assert engine.lookup_policy("p1") == policy
    assert engine.count_policies() == 1


def test_policy_engine_duplicate_policy_exception():
    """Verify ProtectionException on duplicate policy registration."""
    engine = PolicyEngine()
    p1 = ApiPolicy(policy_id="p1", name="P1")
    p2 = ApiPolicy(policy_id="p1", name="P2")

    engine.register_policy(p1)
    with pytest.raises(ProtectionException):
        engine.register_policy(p2)


def test_policy_engine_unregister():
    """Verify unregistering a policy."""
    engine = PolicyEngine()
    policy = ApiPolicy(policy_id="p1", name="P1")
    engine.register_policy(policy)

    removed = engine.unregister_policy("p1")
    assert removed == policy
    assert engine.lookup_policy("p1") is None
    assert engine.count_policies() == 0


def test_policy_engine_evaluate_client_default_allow():
    """Verify client evaluation defaults to ALLOW when no policies block."""
    engine = PolicyEngine()
    ctx = ProtectionContext(context_id="ctx1", client=ClientIdentity(client_id="c1"))

    decision = engine.evaluate_client(ctx)
    assert decision.action == ProtectionDecision.ALLOW


def test_policy_engine_evaluate_client_priority_ordering():
    """Verify policies are evaluated in priority order."""
    engine = PolicyEngine()
    p1 = ApiPolicy(policy_id="p_high", name="HighPriority", priority=10, decision=ProtectionDecision.ALLOW)
    p2 = ApiPolicy(policy_id="p_low", name="LowPriority", priority=50, decision=ProtectionDecision.REJECT)

    engine.register_policy(p2)
    engine.register_policy(p1)

    ctx = ProtectionContext(context_id="ctx1", client=ClientIdentity(client_id="c1"))
    decision = engine.evaluate_client(ctx)

    assert decision.action == ProtectionDecision.ALLOW
    assert decision.policy_id == "p_high"


def test_policy_engine_evaluate_client_throttled_by_rule():
    """Verify client evaluation THROTTLE when embedded rate limit rule is exceeded."""
    limiter = RateLimiter()
    rule = RateLimitRule(rule_id="r1", name="Rule1", max_requests=1, window_seconds=60)
    policy = ApiPolicy(policy_id="p1", name="P1", priority=1, rules=(rule,))

    engine = PolicyEngine(rate_limiter=limiter)
    engine.register_policy(policy)

    ctx = ProtectionContext(context_id="ctx1", client=ClientIdentity(client_id="c1"))
    dec1 = engine.evaluate_client(ctx)
    assert dec1.action == ProtectionDecision.ALLOW

    dec2 = engine.evaluate_client(ctx)
    assert dec2.action == ProtectionDecision.THROTTLE
    assert dec2.rate_limit_decision is not None
    assert dec2.rate_limit_decision.is_allowed is False


def test_policy_engine_evaluate_client_explicit_reject():
    """Verify client evaluation REJECT when policy decision is REJECT."""
    engine = PolicyEngine()
    policy = ApiPolicy(policy_id="p_block", name="Blocker", priority=1, decision=ProtectionDecision.REJECT)
    engine.register_policy(policy)

    ctx = ProtectionContext(context_id="ctx1", client=ClientIdentity(client_id="c1"))
    decision = engine.evaluate_client(ctx)

    assert decision.action == ProtectionDecision.REJECT


def test_policy_engine_clear():
    """Verify clearing policy engine."""
    engine = PolicyEngine()
    engine.register_policy(ApiPolicy(policy_id="p1", name="P1"))
    engine.clear()

    assert engine.count_policies() == 0


# --- ViolationTracker Tests ---

def test_violation_tracker_record_and_list():
    """Verify recording and listing violations."""
    tracker = ViolationTracker()
    viol = ViolationRecord(violation_id="v1", client_id="c1", rule_id="r1", reason="Exceeded limit")
    recorded = tracker.record_violation(viol)

    assert recorded.violation_id == "v1"
    assert tracker.count_violations() == 1
    assert len(tracker.list_violations()) == 1


def test_violation_tracker_list_by_client_id():
    """Verify filtering violations by client ID."""
    tracker = ViolationTracker()
    tracker.record_violation(ViolationRecord(violation_id="v1", client_id="c1", rule_id="r1", reason="R1"))
    tracker.record_violation(ViolationRecord(violation_id="v2", client_id="c2", rule_id="r1", reason="R2"))

    c1_viols = tracker.list_violations(client_id="c1")
    assert len(c1_viols) == 1
    assert c1_viols[0].client_id == "c1"


def test_violation_tracker_is_client_in_cooldown():
    """Verify cooldown check for client."""
    tracker = ViolationTracker()
    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    tracker.record_violation(ViolationRecord(violation_id="v1", client_id="c1", rule_id="r1", reason="R1", cooldown_until=future))

    assert tracker.is_client_in_cooldown("c1") is True
    assert tracker.is_client_in_cooldown("c2") is False


def test_violation_tracker_clear_expired_violations():
    """Verify purging expired violations."""
    tracker = ViolationTracker()
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    future = datetime.now(timezone.utc) + timedelta(minutes=10)

    tracker.record_violation(ViolationRecord(violation_id="v1", client_id="c1", rule_id="r1", reason="R1", cooldown_until=past))
    tracker.record_violation(ViolationRecord(violation_id="v2", client_id="c2", rule_id="r1", reason="R2", cooldown_until=future))

    purged = tracker.clear_expired_violations()
    assert purged == 1
    assert tracker.count_violations() == 1


def test_violation_tracker_clear():
    """Verify clearing violation tracker."""
    tracker = ViolationTracker()
    tracker.record_violation(ViolationRecord(violation_id="v1", client_id="c1", rule_id="r1", reason="R1"))
    tracker.clear()

    assert tracker.count_violations() == 0


# --- ProtectionProvider Tests ---

def test_provider_lifecycle():
    """Verify ProtectionProvider initialize and shutdown transitions."""
    provider = ProtectionProvider()
    assert provider.health().state == ProtectionRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == ProtectionRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == ProtectionRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify ProtectionProvider restart cycle."""
    provider = ProtectionProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == ProtectionRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health_stats_caps_diag():
    """Verify health, statistics, capabilities, and diagnostics from provider."""
    limiter = RateLimiter()
    limiter.register_rule(RateLimitRule(rule_id="r1", name="R1", max_requests=10))

    provider = ProtectionProvider(rate_limiter=limiter)
    provider.initialize()

    assert provider.health().is_healthy is True
    assert provider.statistics().total_rules == 1
    assert provider.capabilities().supports_sliding_window is True
    assert provider.diagnostics().registered_rules_count == 1


# --- ProtectionRuntime Tests ---

def test_runtime_lifecycle_delegation():
    """Verify ProtectionRuntime delegates lifecycle calls to provider."""
    runtime = ProtectionRuntime()
    assert runtime.health().state == ProtectionRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == ProtectionRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == ProtectionRuntimeState.STOPPED


def test_constructor_dependency_injection():
    """Verify Constructor DI in ProtectionProvider and ProtectionRuntime."""
    limiter = RateLimiter()
    engine = PolicyEngine(rate_limiter=limiter)
    tracker = ViolationTracker()

    provider = ProtectionProvider(
        rate_limiter=limiter,
        policy_engine=engine,
        violation_tracker=tracker,
    )
    runtime = ProtectionRuntime(provider=provider)

    assert runtime.get_provider().get_rate_limiter() is limiter
    assert runtime.get_provider().get_policy_engine() is engine
    assert runtime.get_provider().get_violation_tracker() is tracker


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_protection_runtime():
    """Verify get_protection_runtime, set_protection_runtime, and reset_protection_runtime."""
    r1 = get_protection_runtime()
    r2 = get_protection_runtime()
    assert r1 is r2
    assert isinstance(r1, ProtectionRuntime)

    custom = ProtectionRuntime()
    set_protection_runtime(custom)
    assert get_protection_runtime() is custom

    reset_protection_runtime()
    r3 = get_protection_runtime()
    assert r3 is not custom


def test_lazy_singleton_protection_provider():
    """Verify get_protection_provider, set_protection_provider, and reset_protection_provider."""
    p1 = get_protection_provider()
    p2 = get_protection_provider()
    assert p1 is p2
    assert isinstance(p1, ProtectionProvider)

    custom = ProtectionProvider()
    set_protection_provider(custom)
    assert get_protection_provider() is custom

    reset_protection_provider()
    p3 = get_protection_provider()
    assert p3 is not custom


# --- Concurrency Tests ---

def test_concurrent_rate_limiting():
    """Verify thread-safety of RateLimiter under concurrent rate limit evaluations."""
    limiter = RateLimiter()
    limiter.register_rule(RateLimitRule(rule_id="r_shared", name="Shared", max_requests=100, window_seconds=60))

    def eval_worker(idx: int):
        return limiter.evaluate_rate_limit("client_shared", "r_shared")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(eval_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r.is_allowed for r in results)


def test_concurrent_policy_evaluations():
    """Verify thread-safety of PolicyEngine under concurrent policy evaluations."""
    engine = PolicyEngine()
    engine.register_policy(ApiPolicy(policy_id="p1", name="P1", priority=10))

    def policy_worker(idx: int):
        ctx = ProtectionContext(context_id=f"ctx_{idx}", client=ClientIdentity(client_id=f"c_{idx}"))
        return engine.evaluate_client(ctx)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(policy_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r.action == ProtectionDecision.ALLOW for r in results)
