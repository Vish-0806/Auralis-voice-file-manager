"""Unit tests for ClarificationSessionManager and ClarificationSession models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import threading
import time
# pyrefly: ignore [missing-import]
pytest = None
try:
    import pytest
except ImportError:
    pass

from brain.execution.clarification_engine import (
    ClarificationChoice,
    ClarificationEngine,
    ClarificationRequest,
    ClarificationResponse,
    ClarificationType,
)
from brain.execution.clarification_session import (
    ClarificationSession,
    ClarificationSessionConfig,
    ClarificationSessionManager,
    ClarificationSessionStatus,
)
from brain.execution.execution_state import ExecutionStatus
from brain.execution.execution_state_manager import ExecutionStateManager


def _sample_request(req_id: str = "req_1") -> ClarificationRequest:
    """Helper to build a sample ClarificationRequest for testing."""
    return ClarificationRequest(
        clarification_id=req_id,
        type=ClarificationType.CONFIRMATION,
        question="Are you sure you want to delete this folder?",
        choices=[
            ClarificationChoice(id="yes", label="Yes", description="Proceed"),
            ClarificationChoice(id="no", label="No", description="Cancel"),
        ],
        default_choice="no",
        required=True,
        timeout_seconds=30,
    )


def test_create_session() -> None:
    """Verifies that create_session registers a new PENDING session."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_create")
    session = manager.create_session("exec_100", req, timeout_seconds=120)

    assert session is not None
    assert session.session_id.startswith("session_")
    assert session.execution_id == "exec_100"
    assert session.status == ClarificationSessionStatus.PENDING
    assert session.clarification_request.clarification_id == "req_create"
    assert session.expires_at > session.created_at
    assert not session.is_expired()


def test_get_session() -> None:
    """Verifies retrieving a session by session ID."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_get")
    session = manager.create_session("exec_101", req)
    assert session is not None

    fetched = manager.get_session(session.session_id)
    assert fetched is not None
    assert fetched.session_id == session.session_id
    assert fetched.execution_id == "exec_101"


def test_list_pending() -> None:
    """Verifies listing active PENDING sessions."""
    manager = ClarificationSessionManager()
    req1 = _sample_request("req_list_1")
    req2 = _sample_request("req_list_2")

    s1 = manager.create_session("exec_1", req1)
    s2 = manager.create_session("exec_2", req2)

    pending = manager.list_pending()
    assert len(pending) == 2
    session_ids = {s.session_id for s in pending}
    assert s1.session_id in session_ids
    assert s2.session_id in session_ids


def test_submit_valid_response() -> None:
    """Verifies submitting a valid response updates session status to RESPONDED."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_valid")
    session = manager.create_session("exec_200", req)
    assert session is not None

    resp = ClarificationResponse(
        clarification_id="req_valid",
        selected_choice="yes",
        confirmed=True,
        timestamp=time.time(),
    )

    success = manager.submit_response(session.session_id, resp)
    assert success is True

    updated = manager.get_session(session.session_id)
    assert updated is not None
    assert updated.status == ClarificationSessionStatus.RESPONDED
    assert updated.response is not None
    assert updated.response.selected_choice == "yes"


def test_reject_invalid_response() -> None:
    """Verifies submitting an invalid response returns False and keeps state PENDING."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_invalid")
    session = manager.create_session("exec_201", req)
    assert session is not None

    # Invalid choice ID "invalid_option"
    resp = ClarificationResponse(
        clarification_id="req_invalid",
        selected_choice="invalid_option",
        confirmed=False,
        timestamp=time.time(),
    )

    success = manager.submit_response(session.session_id, resp)
    assert success is False

    updated = manager.get_session(session.session_id)
    assert updated is not None
    assert updated.status == ClarificationSessionStatus.PENDING


def test_timeout_expiration() -> None:
    """Verifies session expiration via expire_sessions."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_timeout")
    session = manager.create_session("exec_300", req, timeout_seconds=1)
    assert session is not None

    # Manually expire timestamp to simulate time passing
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=5)

    expired_ids = manager.expire_sessions()
    assert session.session_id in expired_ids

    updated = manager.get_session(session.session_id)
    assert updated is not None
    assert updated.status == ClarificationSessionStatus.TIMED_OUT
    assert manager.list_pending() == []


def test_cancel_session() -> None:
    """Verifies cancelling a session marks it CANCELLED."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_cancel")
    session = manager.create_session("exec_400", req)
    assert session is not None

    result = manager.cancel_session(session.session_id)
    assert result is True

    updated = manager.get_session(session.session_id)
    assert updated is not None
    assert updated.status == ClarificationSessionStatus.CANCELLED


def test_remove_session() -> None:
    """Verifies removing a session from memory."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_remove")
    session = manager.create_session("exec_500", req)
    assert session is not None

    removed = manager.remove_session(session.session_id)
    assert removed is True
    assert manager.get_session(session.session_id) is None


def test_clear_manager() -> None:
    """Verifies clearing all sessions in manager."""
    manager = ClarificationSessionManager()
    manager.create_session("exec_1", _sample_request("r1"))
    manager.create_session("exec_2", _sample_request("r2"))

    assert len(manager.list_pending()) == 2
    manager.clear()
    assert len(manager.list_pending()) == 0


def test_resume_preparation() -> None:
    """Verifies resume_execution applies response and transitions ExecutionState."""
    state_manager = ExecutionStateManager()
    state_manager.create_execution("exec_resume", user_id=1)

    manager = ClarificationSessionManager(state_manager=state_manager)
    req = _sample_request("req_resume")

    session = manager.create_session("exec_resume", req)
    assert session is not None

    exec_state = state_manager.get_execution("exec_resume")
    assert exec_state is not None
    assert exec_state.waiting_for_confirmation is True
    assert exec_state.status == ExecutionStatus.WAITING_FOR_CONFIRMATION

    resp = ClarificationResponse(
        clarification_id="req_resume",
        selected_choice="yes",
        confirmed=True,
        timestamp=time.time(),
    )
    manager.submit_response(session.session_id, resp)

    context = manager.resume_execution(session.session_id)
    assert context is not None
    assert context.metadata.get("resolved_choice") == "yes"
    assert context.metadata.get("confirmed") is True

    assert exec_state.waiting_for_confirmation is False
    assert exec_state.status == ExecutionStatus.RUNNING
    assert session.status == ClarificationSessionStatus.COMPLETED


def test_metadata_preservation() -> None:
    """Verifies custom metadata is preserved in sessions and contexts."""
    manager = ClarificationSessionManager()
    req = _sample_request("req_meta")
    meta = {"source": "voice_command", "priority": "high"}

    session = manager.create_session("exec_meta", req, metadata=meta)
    assert session is not None
    assert session.metadata["source"] == "voice_command"

    resp = ClarificationResponse(
        clarification_id="req_meta",
        selected_choice="yes",
        confirmed=True,
        timestamp=time.time(),
    )
    manager.submit_response(session.session_id, resp)
    ctx = manager.resume_execution(session.session_id)

    assert ctx is not None
    assert ctx.metadata.get("source") == "voice_command"
    assert ctx.metadata.get("resolved_choice") == "yes"


def test_thread_safety() -> None:
    """Verifies concurrent session operations are thread-safe."""
    manager = ClarificationSessionManager()
    errors: list[Exception] = []

    def worker(worker_id: int) -> None:
        try:
            for i in range(10):
                req = _sample_request(f"req_{worker_id}_{i}")
                session = manager.create_session(f"exec_{worker_id}_{i}", req)
                if session:
                    manager.get_session(session.session_id)
                    manager.list_pending()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(manager.list_pending()) == 50


def test_dependency_injection_compatibility() -> None:
    """Verifies dependency injection of custom config, engine, state manager, logger."""
    config = ClarificationSessionConfig(default_timeout_seconds=600, maximum_active_sessions=10)
    engine = ClarificationEngine()
    state_manager = ExecutionStateManager()

    manager = ClarificationSessionManager(config=config, engine=engine, state_manager=state_manager)
    req = _sample_request("req_di")
    session = manager.create_session("exec_di", req)

    assert session is not None
    assert manager._config.default_timeout_seconds == 600
    assert manager._engine is engine
    assert manager._state_manager is state_manager


def test_unknown_session_handling() -> None:
    """Verifies safe handling of unknown or invalid session IDs."""
    manager = ClarificationSessionManager()

    assert manager.get_session("non_existent") is None
    assert manager.submit_response("non_existent", _sample_request("r").default_choice) is False
    assert manager.resume_execution("non_existent") is None
    assert manager.cancel_session("non_existent") is False
    assert manager.remove_session("non_existent") is False
    assert manager.get_session("") is None
    assert manager.get_session(None) is None
