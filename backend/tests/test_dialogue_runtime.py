"""Unit tests for Phase 13.3 – Dialogue Management Runtime."""

import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant.dialogue import (
    DialogueAction,
    DialogueContext,
    DialogueDecision,
    DialogueException,
    DialogueHealth,
    DialogueManager,
    DialogueMode,
    DialoguePolicy,
    DialogueProvider,
    DialogueRuntime,
    DialogueSession,
    DialogueSessionError,
    DialogueState,
    DialogueStateError,
    DialogueStatistics,
    DialogueStatus,
    DialogueTurn,
    IDialogueProvider,
    PolicyManager,
    StateManager,
    get_dialogue_runtime,
    reset_dialogue_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_dialogue_runtime()
    yield
    reset_dialogue_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 8 Pydantic v2 domain models are frozen and immutable."""
    ctx = DialogueContext()
    turn = DialogueTurn()
    state = DialogueState()
    policy = DialoguePolicy()
    dec = DialogueDecision()
    sess = DialogueSession()
    stats = DialogueStatistics()
    health = DialogueHealth()

    models = [ctx, turn, state, policy, dec, sess, stats, health]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.status = DialogueStatus.ERROR  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Dialogue Session & Turn Creation
# ---------------------------------------------------------------------------

def test_session_and_turn_creation() -> None:
    """Verify creating dialogue sessions and appending dialogue turns."""
    runtime = get_dialogue_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DialogueProvider)

    sess = provider.manager.create_session(
        conversation_id="conv-999",
        mode=DialogueMode.INTERACTIVE,
    )
    assert sess.session_id.startswith("dsess-")
    assert sess.conversation_id == "conv-999"
    assert sess.mode == DialogueMode.INTERACTIVE

    turn1 = provider.manager.create_turn(sess.session_id, "Open downloads folder")
    assert turn1.turn_number == 1
    assert turn1.user_input == "Open downloads folder"

    turn2 = provider.manager.create_turn(sess.session_id, "Filter by size")
    assert turn2.turn_number == 2

    session_updated = provider.manager.get_session(sess.session_id)
    assert session_updated is not None
    assert len(session_updated.turns) == 2


# ---------------------------------------------------------------------------
# 3. State Transitions & Validation
# ---------------------------------------------------------------------------

def test_state_transitions() -> None:
    """Verify state machine status updates and invalid transition validation."""
    runtime = get_dialogue_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DialogueProvider)

    sess = provider.manager.create_session()
    sid = sess.session_id

    provider.manager.update_status(sid, DialogueStatus.PROCESSING)
    assert provider.manager.get_session(sid).status == DialogueStatus.PROCESSING

    provider.manager.update_status(sid, DialogueStatus.COMPLETED)
    assert provider.manager.get_session(sid).status == DialogueStatus.COMPLETED

    # Cannot transition out of COMPLETED state
    with pytest.raises(DialogueStateError):
        provider.manager.update_status(sid, DialogueStatus.PROCESSING)

    with pytest.raises(DialogueSessionError):
        provider.manager.update_status("non-existent-id", DialogueStatus.IDLE)


# ---------------------------------------------------------------------------
# 4. Policy Evaluation: Clarification & Confirmation Detection
# ---------------------------------------------------------------------------

def test_policy_evaluation_clarification_and_confirmation() -> None:
    """Verify policy manager evaluation for low confidence and destructive actions."""
    runtime = get_dialogue_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DialogueProvider)

    sess = provider.manager.create_session()

    # Low confidence -> Clarification required
    turn_low = provider.manager.create_turn(sess.session_id, "do something ambiguous", confidence=0.4)
    dec_clarify = provider.policy_manager.evaluate(sess, turn_low)
    assert dec_clarify.action == DialogueAction.CLARIFY
    assert dec_clarify.requires_clarification is True
    assert "clarify" in dec_clarify.clarification_prompt.lower()

    # Destructive operation -> Confirmation required
    turn_del = provider.manager.create_turn(sess.session_id, "delete all temporary files", confidence=1.0)
    dec_confirm = provider.policy_manager.evaluate(sess, turn_del)
    assert dec_confirm.action == DialogueAction.CONFIRM
    assert dec_confirm.requires_confirmation is True
    assert "confirmation" in dec_confirm.confirmation_prompt.lower()

    # Standard query -> Normal response
    turn_norm = provider.manager.create_turn(sess.session_id, "list desktop files", confidence=1.0)
    dec_norm = provider.policy_manager.evaluate(sess, turn_norm)
    assert dec_norm.action == DialogueAction.RESPOND
    assert dec_norm.requires_clarification is False
    assert dec_norm.requires_confirmation is False


# ---------------------------------------------------------------------------
# 5. State Manager & Context Merging
# ---------------------------------------------------------------------------

def test_state_manager_and_context_updates() -> None:
    """Verify StateManager records turns, updates snapshots, and merges context."""
    runtime = get_dialogue_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DialogueProvider)

    sess = provider.manager.create_session()
    sid = sess.session_id
    turn = provider.manager.create_turn(sid, "Show system details")

    provider.state_manager.record_turn(sid, turn)
    state = provider.state_manager.get_state(sid)

    assert state is not None
    assert state.turn_count == 1
    assert state.current_turn.turn_id == turn.turn_id

    ctx = provider.state_manager.update_context(sid, {"intent": "show_details", "slot": "system"})
    assert ctx.variables["intent"] == "show_details"


# ---------------------------------------------------------------------------
# 6. Statistics & Health Reporting
# ---------------------------------------------------------------------------

def test_statistics_and_health() -> None:
    """Verify dialogue subsystem statistics and diagnostic health snapshot."""
    runtime = get_dialogue_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DialogueProvider)

    s1 = provider.manager.create_session()
    t1 = provider.manager.create_turn(s1.session_id, "delete temp", confidence=1.0)
    t2 = provider.manager.create_turn(s1.session_id, "what?", confidence=0.2)

    # Evaluate turns to record clarification/confirmation count stats
    _ = provider.policy_manager.evaluate(s1, t1)
    _ = provider.policy_manager.evaluate(s1, t2)

    stats = runtime.get_statistics()
    assert stats.total_sessions_created == 1
    assert stats.total_turns_processed == 2

    health = runtime.get_health()
    assert health.healthy is True
    assert health.status == "READY"


# ---------------------------------------------------------------------------
# 7. Singleton Identity & Reset
# ---------------------------------------------------------------------------

def test_singleton_identity() -> None:
    """Verify get_dialogue_runtime identity and reset_dialogue_runtime."""
    rt1 = get_dialogue_runtime()
    rt2 = get_dialogue_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    reset_dialogue_runtime()
    rt3 = get_dialogue_runtime()
    assert rt3 is not rt1
    assert rt3.is_initialized is True


# ---------------------------------------------------------------------------
# 8. Thread Safety
# ---------------------------------------------------------------------------

def test_thread_safety() -> None:
    """Verify thread safety during concurrent dialogue session and turn operations."""
    runtime = get_dialogue_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DialogueProvider)

    errors = []

    def worker(idx: int) -> None:
        try:
            sess = provider.manager.create_session(conversation_id=f"conv-{idx}")
            for i in range(10):
                turn = provider.manager.create_turn(sess.session_id, f"Turn {i} thread {idx}")
                dec = provider.policy_manager.evaluate(sess, turn)
                provider.state_manager.record_turn(sess.session_id, turn)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    stats = runtime.get_statistics()
    assert stats.total_sessions_created == 10
    assert stats.total_turns_processed == 100


# ---------------------------------------------------------------------------
# 9. Dependency Injection
# ---------------------------------------------------------------------------

def test_dependency_injection() -> None:
    """Verify constructor dependency injection for managers."""
    custom_mgr = DialogueManager()
    custom_policy = PolicyManager()
    custom_state = StateManager()

    provider = DialogueProvider(
        manager=custom_mgr,
        policy_manager=custom_policy,
        state_manager=custom_state,
    )
    runtime = DialogueRuntime(provider=provider)
    runtime.initialize()

    assert provider.manager is custom_mgr
    assert provider.policy_manager is custom_policy
    assert provider.state_manager is custom_state


# ---------------------------------------------------------------------------
# 10. Backward Compatibility
# ---------------------------------------------------------------------------

def test_backward_compatibility() -> None:
    """Verify Phase 9 AssistantRuntime and Phase 13.2 ConversationRuntime operate in parallel."""
    from brain.assistant.conversation import get_conversation_runtime
    from brain.runtime import AssistantRuntime as Phase9Runtime

    p9 = Phase9Runtime()
    assert p9.initialize() is True

    conv_rt = get_conversation_runtime()
    assert conv_rt.is_initialized is True

    assert p9.shutdown() is True
