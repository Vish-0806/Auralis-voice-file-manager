"""Unit tests for ClarificationManager (Phase 9.6)."""

import time
# pyrefly: ignore [missing-import]
import pytest
from brain.voice import ClarificationManager, ClarificationStatus, VoiceClarification


@pytest.fixture
def manager() -> ClarificationManager:
    return ClarificationManager(default_timeout_seconds=0.5)


# ---------------------------------------------------------------------------
# Request Clarification
# ---------------------------------------------------------------------------

def test_request_clarification_creates_pending(manager: ClarificationManager) -> None:
    clar = manager.request_clarification(
        session_id="s1",
        prompt="Which file?",
        options=["file1.txt", "file2.txt"],
        command_id="cmd-1",
    )
    assert isinstance(clar, VoiceClarification)
    assert clar.status == ClarificationStatus.PENDING
    assert clar.session_id == "s1"
    assert clar.prompt == "Which file?"
    assert clar.options == ["file1.txt", "file2.txt"]
    assert clar.command_id == "cmd-1"
    assert clar.clarification_id.startswith("clar-")


def test_request_clarification_custom_timeout(manager: ClarificationManager) -> None:
    clar = manager.request_clarification("s1", "Which one?", ["a", "b"], timeout_seconds=15.0)
    assert clar.timeout_seconds == 15.0


# ---------------------------------------------------------------------------
# Receive Response / Cancel
# ---------------------------------------------------------------------------

def test_receive_response(manager: ClarificationManager) -> None:
    clar = manager.request_clarification("s1", "Which?", ["a", "b"])
    res = manager.receive_response(clar.clarification_id, selected_option="a")
    assert res.status == ClarificationStatus.RECEIVED
    assert res.selected_option == "a"
    assert res.resolved_at is not None


def test_cancel_clarification(manager: ClarificationManager) -> None:
    clar = manager.request_clarification("s1", "Which?", ["a", "b"])
    res = manager.cancel(clar.clarification_id)
    assert res.status == ClarificationStatus.CANCELLED
    assert res.selected_option is None
    assert res.resolved_at is not None


def test_receive_response_already_resolved(manager: ClarificationManager) -> None:
    clar = manager.request_clarification("s1", "Which?", ["a", "b"])
    manager.receive_response(clar.clarification_id, selected_option="a")
    second = manager.receive_response(clar.clarification_id, selected_option="b")
    assert second.selected_option == "a"


def test_receive_response_unknown(manager: ClarificationManager) -> None:
    res = manager.receive_response("ghost-id", selected_option="x")
    assert res.status == ClarificationStatus.RECEIVED
    assert res.metadata.get("error") == "not_found"


# ---------------------------------------------------------------------------
# Timeouts & Lookup & Prompts
# ---------------------------------------------------------------------------

def test_check_timeouts_marks_expired(manager: ClarificationManager) -> None:
    clar = manager.request_clarification("s1", "Prompt", ["a"], timeout_seconds=0.01)
    time.sleep(0.05)
    expired = manager.check_timeouts()
    assert len(expired) == 1
    assert expired[0].clarification_id == clar.clarification_id
    assert expired[0].status == ClarificationStatus.TIMED_OUT


def test_get_clarification_lazy_timeout(manager: ClarificationManager) -> None:
    clar = manager.request_clarification("s1", "Prompt", ["a"], timeout_seconds=0.01)
    time.sleep(0.05)
    fetched = manager.get_clarification(clar.clarification_id)
    assert fetched is not None
    assert fetched.status == ClarificationStatus.TIMED_OUT


def test_get_clarification_unknown(manager: ClarificationManager) -> None:
    assert manager.get_clarification("unknown") is None


def test_get_history(manager: ClarificationManager) -> None:
    c1 = manager.request_clarification("s1", "P1", ["a"])
    c2 = manager.request_clarification("s1", "P2", ["b"])
    c3 = manager.request_clarification("s2", "P3", ["c"])
    
    h1 = manager.get_history("s1")
    assert len(h1) == 2
    assert [c.clarification_id for c in h1] == [c1.clarification_id, c2.clarification_id]


def test_build_prompt(manager: ClarificationManager) -> None:
    assert manager.build_prompt([]) == "Which item did you mean?"
    assert manager.build_prompt(["doc.txt"]) == 'Did you mean "doc.txt"?'
    p = manager.build_prompt(["doc.txt", "doc.pdf"], action="delete")
    assert 'delete "doc.txt" or "doc.pdf"' in p


def test_clear_session(manager: ClarificationManager) -> None:
    c1 = manager.request_clarification("s1", "P1", ["a"])
    manager.clear_session("s1")
    assert manager.get_clarification(c1.clarification_id) is None
    assert manager.get_history("s1") == []


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_clarification_manager_thread_safety(manager: ClarificationManager) -> None:
    import threading
    clars = []

    def req(i: int) -> None:
        c = manager.request_clarification("s-concur", f"Prompt {i}", [f"opt{i}"])
        clars.append(c)

    threads = [threading.Thread(target=req, args=(i,)) for i in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(clars) == 30
    assert len(manager.get_history("s-concur")) == 30
