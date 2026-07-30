"""Unit tests for VoiceOrchestrator (Phase 9.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.voice import (
    VoiceOrchestrator, VoiceCommand, VoiceCommandStatus,
    VoiceInteractionType, VoiceSessionState,
)


@pytest.fixture
def orchestrator() -> VoiceOrchestrator:
    return VoiceOrchestrator()


# ---------------------------------------------------------------------------
# Session Operations
# ---------------------------------------------------------------------------

def test_create_and_get_session(orchestrator: VoiceOrchestrator) -> None:
    session = orchestrator.create_session("s1", conversation_id="conv-1")
    assert session.session_id == "s1"
    assert session.conversation_id == "conv-1"
    assert orchestrator.get_session("s1") is session
    assert orchestrator.get_session_state("s1") == VoiceSessionState.ACTIVE


def test_list_sessions(orchestrator: VoiceOrchestrator) -> None:
    orchestrator.create_session("s1")
    orchestrator.create_session("s2")
    sessions = orchestrator.list_sessions()
    assert "s1" in sessions
    assert "s2" in sessions


# ---------------------------------------------------------------------------
# Command Processing
# ---------------------------------------------------------------------------

def test_process_normal_command(orchestrator: VoiceOrchestrator) -> None:
    cmd = VoiceCommand(command_id="c1", session_id="s1", raw_text="search documents")
    res = orchestrator.process_command(cmd)
    assert res.success is True
    assert res.status == VoiceCommandStatus.COMPLETED
    assert res.feedback is not None
    assert "Search completed" in res.feedback.text


def test_process_command_requiring_confirmation(orchestrator: VoiceOrchestrator) -> None:
    cmd = VoiceCommand(
        command_id="c1",
        session_id="s1",
        raw_text="delete downloads",
        requires_confirmation=True,
    )
    res = orchestrator.process_command(cmd)
    assert res.success is True
    assert res.status == VoiceCommandStatus.PENDING
    assert res.confirmation_required is True
    assert orchestrator.get_session_state("s1") == VoiceSessionState.CONFIRMING


def test_process_command_requiring_clarification(orchestrator: VoiceOrchestrator) -> None:
    cmd = VoiceCommand(
        command_id="c1",
        session_id="s1",
        raw_text="open report",
        requires_clarification=True,
        metadata={"clarification_options": ["report.pdf", "report.docx"]},
    )
    res = orchestrator.process_command(cmd)
    assert res.success is True
    assert res.status == VoiceCommandStatus.PENDING
    assert res.clarification_required is True
    assert orchestrator.get_session_state("s1") == VoiceSessionState.CLARIFYING


# ---------------------------------------------------------------------------
# Confirm & Clarify
# ---------------------------------------------------------------------------

def test_confirm_accept(orchestrator: VoiceOrchestrator) -> None:
    cmd = VoiceCommand(command_id="c1", session_id="s1", requires_confirmation=True)
    res = orchestrator.process_command(cmd)
    session = orchestrator.get_session("s1")
    conf_id = session.pending_confirmation.confirmation_id

    resp = orchestrator.confirm("s1", conf_id, accepted=True)
    assert resp.success is True
    assert resp.interaction_type == VoiceInteractionType.CONFIRMATION
    assert session.pending_confirmation is None


def test_confirm_reject(orchestrator: VoiceOrchestrator) -> None:
    cmd = VoiceCommand(command_id="c1", session_id="s1", requires_confirmation=True)
    orchestrator.process_command(cmd)
    session = orchestrator.get_session("s1")
    conf_id = session.pending_confirmation.confirmation_id

    resp = orchestrator.confirm("s1", conf_id, accepted=False)
    assert resp.success is False
    assert session.pending_confirmation is None


def test_clarify_selection(orchestrator: VoiceOrchestrator) -> None:
    cmd = VoiceCommand(
        command_id="c1", session_id="s1", requires_clarification=True,
        metadata={"clarification_options": ["a", "b"]},
    )
    orchestrator.process_command(cmd)
    session = orchestrator.get_session("s1")
    clar_id = session.pending_clarification.clarification_id

    resp = orchestrator.clarify("s1", clar_id, selected_option="a")
    assert resp.success is True
    assert resp.interaction_type == VoiceInteractionType.CLARIFICATION
    assert 'Using "a"' in resp.text
    assert session.pending_clarification is None


# ---------------------------------------------------------------------------
# Session Cancellation & Ending
# ---------------------------------------------------------------------------

def test_cancel_session(orchestrator: VoiceOrchestrator) -> None:
    orchestrator.create_session("s1")
    resp = orchestrator.cancel_session("s1")
    assert resp.success is True
    assert resp.interaction_type == VoiceInteractionType.CANCELLATION
    assert orchestrator.get_session_state("s1") == VoiceSessionState.ENDED


def test_end_session(orchestrator: VoiceOrchestrator) -> None:
    orchestrator.create_session("s1")
    ended = orchestrator.end_session("s1")
    assert ended is True
    assert orchestrator.get_session_state("s1") == VoiceSessionState.ENDED


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_voice_orchestrator_thread_safety(orchestrator: VoiceOrchestrator) -> None:
    import threading
    results = []

    def run(i: int) -> None:
        cmd = VoiceCommand(command_id=f"cmd-{i}", session_id=f"s-{i}", raw_text=f"test {i}")
        res = orchestrator.process_command(cmd)
        results.append(res)

    threads = [threading.Thread(target=run, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert len(orchestrator.list_sessions()) == 20
