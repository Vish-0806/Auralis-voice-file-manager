"""Unit tests for VoiceSession (Phase 9.6)."""

import threading
# pyrefly: ignore [missing-import]
import pytest

from brain.voice import (
    VoiceCommand, VoiceCommandStatus,
    VoiceConfirmation, ConfirmationStatus,
    VoiceClarification, ClarificationStatus,
    VoiceSessionState,
)
from brain.voice.voice_session import VoiceSession


@pytest.fixture
def session() -> VoiceSession:
    s = VoiceSession(session_id="test-session")
    return s


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_session_default_id() -> None:
    s = VoiceSession()
    assert s.session_id.startswith("vs-")


def test_session_explicit_id() -> None:
    s = VoiceSession(session_id="my-session")
    assert s.session_id == "my-session"


def test_session_initial_state_is_idle(session: VoiceSession) -> None:
    assert session.state == VoiceSessionState.IDLE


def test_session_with_conversation_id() -> None:
    s = VoiceSession(conversation_id="conv-123")
    assert s.conversation_id == "conv-123"


def test_session_conversation_id_none_by_default(session: VoiceSession) -> None:
    assert session.conversation_id is None


# ---------------------------------------------------------------------------
# State Transitions
# ---------------------------------------------------------------------------

def test_transition_idle_to_active(session: VoiceSession) -> None:
    result = session.transition_state(VoiceSessionState.ACTIVE)
    assert result is True
    assert session.state == VoiceSessionState.ACTIVE


def test_transition_idle_to_ended(session: VoiceSession) -> None:
    result = session.transition_state(VoiceSessionState.ENDED)
    assert result is True


def test_transition_active_to_processing(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    result = session.transition_state(VoiceSessionState.PROCESSING)
    assert result is True
    assert session.state == VoiceSessionState.PROCESSING


def test_transition_active_to_confirming(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    result = session.transition_state(VoiceSessionState.CONFIRMING)
    assert result is True


def test_transition_active_to_clarifying(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    result = session.transition_state(VoiceSessionState.CLARIFYING)
    assert result is True


def test_invalid_transition_processing_to_confirming(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    session.transition_state(VoiceSessionState.PROCESSING)
    result = session.transition_state(VoiceSessionState.CONFIRMING)
    assert result is False


def test_ended_state_no_further_transitions(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ENDED)
    result = session.transition_state(VoiceSessionState.ACTIVE)
    assert result is False
    assert session.state == VoiceSessionState.ENDED


def test_force_state_bypasses_validation(session: VoiceSession) -> None:
    session.force_state(VoiceSessionState.PROCESSING)
    assert session.state == VoiceSessionState.PROCESSING


def test_ended_at_set_on_end_state(session: VoiceSession) -> None:
    assert session.ended_at is None
    session.transition_state(VoiceSessionState.ENDED)
    assert session.ended_at is not None


# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------

def test_set_pending_confirmation_transitions_to_confirming(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    conf = VoiceConfirmation(confirmation_id="c1", prompt="Sure?")
    session.set_pending_confirmation(conf)
    assert session.state == VoiceSessionState.CONFIRMING
    assert session.pending_confirmation is not None
    assert session.pending_confirmation.confirmation_id == "c1"


def test_clear_pending_confirmation_returns_to_active(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    session.set_pending_confirmation(VoiceConfirmation(confirmation_id="c1"))
    session.clear_pending_confirmation()
    assert session.pending_confirmation is None
    assert session.state == VoiceSessionState.ACTIVE


# ---------------------------------------------------------------------------
# Clarification
# ---------------------------------------------------------------------------

def test_set_pending_clarification_transitions_to_clarifying(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    clar = VoiceClarification(clarification_id="cl1", prompt="Which one?", options=["a", "b"])
    session.set_pending_clarification(clar)
    assert session.state == VoiceSessionState.CLARIFYING
    assert session.pending_clarification is not None


def test_clear_pending_clarification_returns_to_active(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    session.set_pending_clarification(VoiceClarification(clarification_id="cl1"))
    session.clear_pending_clarification()
    assert session.pending_clarification is None
    assert session.state == VoiceSessionState.ACTIVE


# ---------------------------------------------------------------------------
# Command History
# ---------------------------------------------------------------------------

def test_record_command_adds_to_history(session: VoiceSession) -> None:
    cmd = VoiceCommand(command_id="cmd1", raw_text="search downloads")
    session.record_command(cmd)
    history = session.get_command_history()
    assert len(history) == 1
    assert history[0].command_id == "cmd1"


def test_record_multiple_commands(session: VoiceSession) -> None:
    for i in range(5):
        session.record_command(VoiceCommand(command_id=f"cmd{i}"))
    assert len(session.get_command_history()) == 5


def test_get_command_history_returns_copy(session: VoiceSession) -> None:
    cmd = VoiceCommand(command_id="c1")
    session.record_command(cmd)
    h = session.get_command_history()
    h.clear()
    assert len(session.get_command_history()) == 1


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def test_cancel_ends_session(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    session.cancel()
    assert session.is_ended()


def test_cancel_clears_pending_state(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    session.set_pending_confirmation(VoiceConfirmation(confirmation_id="c1"))
    session.cancel()
    assert session.pending_confirmation is None


def test_cancel_is_idempotent(session: VoiceSession) -> None:
    session.cancel()
    session.cancel()
    assert session.is_ended()


def test_end_ends_session(session: VoiceSession) -> None:
    session.end()
    assert session.is_ended()


# ---------------------------------------------------------------------------
# State Helpers
# ---------------------------------------------------------------------------

def test_is_active_true_when_active(session: VoiceSession) -> None:
    session.transition_state(VoiceSessionState.ACTIVE)
    assert session.is_active() is True


def test_is_active_false_when_idle(session: VoiceSession) -> None:
    assert session.is_active() is False


def test_is_idle_true_initially(session: VoiceSession) -> None:
    assert session.is_idle() is True


def test_is_processing(session: VoiceSession) -> None:
    session.force_state(VoiceSessionState.PROCESSING)
    assert session.is_processing() is True


def test_is_ended(session: VoiceSession) -> None:
    session.end()
    assert session.is_ended() is True


def test_summary_returns_dict(session: VoiceSession) -> None:
    s = session.summary()
    assert "session_id" in s
    assert s["session_id"] == "test-session"
    assert "state" in s


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_session_thread_safe_record_commands() -> None:
    s = VoiceSession()
    results = []

    def add(i: int) -> None:
        s.record_command(VoiceCommand(command_id=f"cmd{i}"))
        results.append(i)

    threads = [threading.Thread(target=add, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(s.get_command_history()) == 50
