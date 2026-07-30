"""Unit tests for ConfirmationManager (Phase 9.6)."""

import time
from datetime import datetime, timezone, timedelta
# pyrefly: ignore [missing-import]
import pytest
from brain.voice import ConfirmationManager, ConfirmationStatus, VoiceConfirmation


@pytest.fixture
def manager() -> ConfirmationManager:
    return ConfirmationManager(default_timeout_seconds=0.5)


# ---------------------------------------------------------------------------
# Request Confirmation
# ---------------------------------------------------------------------------

def test_request_confirmation_creates_pending(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation(
        session_id="s1",
        prompt="Delete all files?",
        command_id="cmd-1",
    )
    assert isinstance(conf, VoiceConfirmation)
    assert conf.status == ConfirmationStatus.PENDING
    assert conf.session_id == "s1"
    assert conf.prompt == "Delete all files?"
    assert conf.command_id == "cmd-1"
    assert conf.confirmation_id.startswith("conf-")


def test_request_confirmation_custom_timeout(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation("s1", "Sure?", timeout_seconds=10.0)
    assert conf.timeout_seconds == 10.0


# ---------------------------------------------------------------------------
# Accept / Reject / Cancel
# ---------------------------------------------------------------------------

def test_accept_confirmation(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation("s1", "Are you sure?")
    res = manager.accept(conf.confirmation_id)
    assert res.status == ConfirmationStatus.ACCEPTED
    assert res.response is True
    assert res.resolved_at is not None


def test_reject_confirmation(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation("s1", "Are you sure?")
    res = manager.reject(conf.confirmation_id)
    assert res.status == ConfirmationStatus.REJECTED
    assert res.response is False
    assert res.resolved_at is not None


def test_cancel_confirmation(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation("s1", "Are you sure?")
    res = manager.cancel(conf.confirmation_id)
    assert res.status == ConfirmationStatus.CANCELLED
    assert res.response is None
    assert res.resolved_at is not None


def test_resolve_already_resolved_is_noop(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation("s1", "Are you sure?")
    first = manager.accept(conf.confirmation_id)
    second = manager.reject(conf.confirmation_id)
    assert second.status == ConfirmationStatus.ACCEPTED


def test_resolve_unknown_confirmation(manager: ConfirmationManager) -> None:
    res = manager.accept("ghost-id")
    assert res.status == ConfirmationStatus.ACCEPTED
    assert res.metadata.get("error") == "not_found"


# ---------------------------------------------------------------------------
# Timeouts & Lookup
# ---------------------------------------------------------------------------

def test_check_timeouts_marks_expired(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation("s1", "Prompt", timeout_seconds=0.01)
    time.sleep(0.05)
    expired = manager.check_timeouts()
    assert len(expired) == 1
    assert expired[0].confirmation_id == conf.confirmation_id
    assert expired[0].status == ConfirmationStatus.TIMED_OUT


def test_get_confirmation_lazy_timeout(manager: ConfirmationManager) -> None:
    conf = manager.request_confirmation("s1", "Prompt", timeout_seconds=0.01)
    time.sleep(0.05)
    fetched = manager.get_confirmation(conf.confirmation_id)
    assert fetched is not None
    assert fetched.status == ConfirmationStatus.TIMED_OUT


def test_get_confirmation_unknown(manager: ConfirmationManager) -> None:
    assert manager.get_confirmation("unknown") is None


def test_get_history(manager: ConfirmationManager) -> None:
    c1 = manager.request_confirmation("s1", "P1")
    c2 = manager.request_confirmation("s1", "P2")
    c3 = manager.request_confirmation("s2", "P3")
    
    h1 = manager.get_history("s1")
    assert len(h1) == 2
    assert [c.confirmation_id for c in h1] == [c1.confirmation_id, c2.confirmation_id]


def test_clear_session(manager: ConfirmationManager) -> None:
    c1 = manager.request_confirmation("s1", "P1")
    manager.clear_session("s1")
    assert manager.get_confirmation(c1.confirmation_id) is None
    assert manager.get_history("s1") == []


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_confirmation_manager_thread_safety(manager: ConfirmationManager) -> None:
    import threading
    confs = []

    def req(i: int) -> None:
        c = manager.request_confirmation("s-concur", f"Prompt {i}")
        confs.append(c)

    threads = [threading.Thread(target=req, args=(i,)) for i in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(confs) == 30
    assert len(manager.get_history("s-concur")) == 30
