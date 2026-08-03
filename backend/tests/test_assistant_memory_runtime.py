"""Unit tests for Phase 13.5 – Assistant Memory & Context Integration Runtime."""

import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant.memory import (
    AssistantContextManager,
    AssistantContextPriority,
    AssistantConversationSummary,
    AssistantMemoryContext,
    AssistantMemoryException,
    AssistantMemoryHealth,
    AssistantMemoryProvider,
    AssistantMemoryReference,
    AssistantMemoryRuntime,
    AssistantMemoryScope,
    AssistantMemorySnapshot,
    AssistantMemorySource,
    AssistantMemoryStatistics,
    AssistantPreference,
    AssistantWorkingContext,
    IAssistantMemoryProvider,
    MemoryCoordinator,
    PreferenceManager,
    get_assistant_memory_runtime,
    reset_assistant_memory_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_assistant_memory_runtime()
    yield
    reset_assistant_memory_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 8 Pydantic v2 models are frozen and immutable."""
    ref = AssistantMemoryReference()
    summary = AssistantConversationSummary()
    pref = AssistantPreference()
    ctx = AssistantMemoryContext()
    working_ctx = AssistantWorkingContext()
    snapshot = AssistantMemorySnapshot()
    stats = AssistantMemoryStatistics()
    health = AssistantMemoryHealth()

    models = [ref, summary, pref, ctx, working_ctx, snapshot, stats, health]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.tokens_estimate = 999  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Context Retrieval & Multi-Source Merge
# ---------------------------------------------------------------------------

def test_context_merge_and_priority_ordering() -> None:
    """Verify ContextManager prioritizes context units (MANDATORY > HIGH > LOW) and deduplicates payload keys."""
    mgr = AssistantContextManager()

    ctx_low = AssistantMemoryContext(
        context_id="c-low",
        priority=AssistantContextPriority.LOW,
        payload={"theme": "light", "user": "alice"},
        tokens_estimate=10,
    )
    ctx_mandatory = AssistantMemoryContext(
        context_id="c-mand",
        priority=AssistantContextPriority.MANDATORY,
        payload={"theme": "dark", "session_token": "abc1234"},
        tokens_estimate=15,
    )

    working_ctx = mgr.merge_contexts([ctx_low, ctx_mandatory], token_budget=4096)

    assert isinstance(working_ctx, AssistantWorkingContext)
    # Higher priority (MANDATORY) theme="dark" must overwrite lower priority (LOW) theme="light"
    assert working_ctx.merged_variables["theme"] == "dark"
    assert working_ctx.merged_variables["user"] == "alice"
    assert working_ctx.prioritized_contexts[0].context_id == "c-mand"


# ---------------------------------------------------------------------------
# 3. Preference Retrieval & Scope Hierarchy
# ---------------------------------------------------------------------------

def test_preference_retrieval_and_overrides() -> None:
    """Verify preference merging hierarchy: runtime < assistant < user."""
    pref_mgr = PreferenceManager()

    pref_mgr.register_preference(AssistantPreference(key="default_mode", value="standard"))

    merged = pref_mgr.merge_preferences(
        runtime_prefs={"default_mode": "runtime_override", "timeout": 30},
        assistant_prefs={"timeout": 60, "theme": "blue"},
        user_prefs={"theme": "dark"},
    )

    assert merged["default_mode"] == "runtime_override"
    assert merged["timeout"] == 60
    assert merged["theme"] == "dark"


# ---------------------------------------------------------------------------
# 4. Token Budgeting & Trimming
# ---------------------------------------------------------------------------

def test_token_budgeting_and_trimming() -> None:
    """Verify token budgeting truncates lower priority contexts when budget is exceeded."""
    mgr = AssistantContextManager()

    ctx1 = AssistantMemoryContext(
        priority=AssistantContextPriority.MANDATORY,
        payload={"k1": "v1"},
        tokens_estimate=100,
    )
    ctx2 = AssistantMemoryContext(
        priority=AssistantContextPriority.LOW,
        payload={"k2": "v2"},
        tokens_estimate=300,
    )

    working_ctx = mgr.merge_contexts([ctx1, ctx2], token_budget=200)

    assert working_ctx.trimmed is True
    assert len(working_ctx.prioritized_contexts) == 1
    assert working_ctx.prioritized_contexts[0].priority == AssistantContextPriority.MANDATORY


# ---------------------------------------------------------------------------
# 5. Coordinator Snapshot Generation
# ---------------------------------------------------------------------------

def test_coordinator_snapshot_generation() -> None:
    """Verify MemoryCoordinator creates unified AssistantMemorySnapshot across runtimes."""
    coord = MemoryCoordinator()

    class DummyConvRuntime:
        def get_statistics(self):
            class DummyStats:
                active_conversations = 2
                total_messages_processed = 14
            return DummyStats()

    class DummyDialogueRuntime:
        def get_health(self):
            class DummyHealth:
                status = "READY"
            return DummyHealth()

    class DummyDecisionRuntime:
        def get_statistics(self):
            class DummyStats:
                total_requests_evaluated = 5
            return DummyStats()

    snapshot = coord.create_snapshot(
        session_id="sess-999",
        conversation_runtime=DummyConvRuntime(),
        dialogue_runtime=DummyDialogueRuntime(),
        decision_runtime=DummyDecisionRuntime(),
        token_budget=2048,
    )

    assert isinstance(snapshot, AssistantMemorySnapshot)
    assert snapshot.session_id == "sess-999"
    assert snapshot.dialogue_status == "READY"
    assert snapshot.last_decision_action == "EVALUATED"
    assert len(snapshot.references) >= 2


# ---------------------------------------------------------------------------
# 6. Statistics & Health Reporting
# ---------------------------------------------------------------------------

def test_statistics_and_health() -> None:
    """Verify memory integration subsystem statistics and diagnostic health."""
    runtime = get_assistant_memory_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, AssistantMemoryProvider)

    snapshot = provider.create_snapshot(session_id="sess-test")
    assert snapshot is not None

    stats = runtime.get_statistics()
    assert stats.total_snapshots_generated == 1
    assert stats.total_context_merges == 1

    health = runtime.get_health()
    assert health.healthy is True
    assert health.status == "READY"


# ---------------------------------------------------------------------------
# 7. Singleton Identity & Reset
# ---------------------------------------------------------------------------

def test_singleton_identity() -> None:
    """Verify get_assistant_memory_runtime singleton identity and reset mechanics."""
    rt1 = get_assistant_memory_runtime()
    rt2 = get_assistant_memory_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    reset_assistant_memory_runtime()
    rt3 = get_assistant_memory_runtime()
    assert rt3 is not rt1
    assert rt3.is_initialized is True


# ---------------------------------------------------------------------------
# 8. Thread Safety
# ---------------------------------------------------------------------------

def test_thread_safety() -> None:
    """Verify thread safety during concurrent context merges and snapshot generation."""
    runtime = get_assistant_memory_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, AssistantMemoryProvider)

    errors = []

    def worker(idx: int) -> None:
        try:
            for i in range(10):
                ctx1 = AssistantMemoryContext(
                    priority=AssistantContextPriority.HIGH,
                    payload={f"key_{idx}_{i}": f"val_{i}"},
                    tokens_estimate=10,
                )
                _ = provider.context_manager.merge_contexts([ctx1], session_id=f"s-{idx}")
                _ = provider.preference_manager.merge_preferences(user_prefs={f"p_{idx}": i})
                _ = provider.create_snapshot(session_id=f"s-{idx}")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    stats = runtime.get_statistics()
    assert stats.total_snapshots_generated == 100


# ---------------------------------------------------------------------------
# 9. Dependency Injection & Backward Compatibility
# ---------------------------------------------------------------------------

def test_dependency_injection_and_compatibility() -> None:
    """Verify constructor dependency injection and backward compatibility with Phase 10.5 & Phase 13.1-13.4."""
    from brain.assistant import get_assistant_runtime
    from brain.assistant.conversation import get_conversation_runtime
    from brain.assistant.dialogue import get_dialogue_runtime
    from brain.assistant.reasoning import get_decision_runtime

    ast_rt = get_assistant_runtime()
    conv_rt = get_conversation_runtime()
    dial_rt = get_dialogue_runtime()
    dec_rt = get_decision_runtime()

    assert ast_rt.is_initialized is True
    assert conv_rt.is_initialized is True
    assert dial_rt.is_initialized is True
    assert dec_rt.is_initialized is True

    custom_ctx = AssistantContextManager()
    custom_pref = PreferenceManager()
    custom_coord = MemoryCoordinator(context_manager=custom_ctx)

    provider = AssistantMemoryProvider(
        context_manager=custom_ctx,
        preference_manager=custom_pref,
        coordinator=custom_coord,
    )

    mem_rt = AssistantMemoryRuntime(provider=provider)
    mem_rt.initialize()
    assert mem_rt.is_initialized is True
