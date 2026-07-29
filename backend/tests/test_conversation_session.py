"""Unit tests for ConversationSessionManager (Phase 9.1.1)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.conversation.conversation_session import (
    ConversationSession,
    ConversationSessionConfig,
    ConversationSessionManager,
    ConversationSessionStatus,
    ConversationTurn,
)


@pytest.fixture
def manager() -> ConversationSessionManager:
    """Fixture providing a fresh ConversationSessionManager instance."""
    return ConversationSessionManager()


def test_create_session(manager: ConversationSessionManager) -> None:
    """Verifies successful creation of a session with ACTIVE status."""
    session = manager.create_session(
        user_id="user_123",
        title="Test Session",
        metadata={"source": "unit_test"},
    )

    assert session.session_id.startswith("session_")
    assert session.user_id == "user_123"
    assert session.title == "Test Session"
    assert session.status == ConversationSessionStatus.ACTIVE
    assert session.metadata == {"source": "unit_test"}
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)
    assert isinstance(session.last_activity, datetime)


def test_get_session(manager: ConversationSessionManager) -> None:
    """Verifies getting an active or historical session by ID."""
    session = manager.create_session(user_id="user_123")

    retrieved = manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.user_id == "user_123"


def test_list_sessions(manager: ConversationSessionManager) -> None:
    """Verifies list_sessions and list_active_sessions with user filtering."""
    s1 = manager.create_session(user_id="user_A")
    s2 = manager.create_session(user_id="user_B")
    s3 = manager.create_session(user_id="user_A")

    all_sessions = manager.list_sessions()
    assert len(all_sessions) == 3

    user_a_sessions = manager.list_sessions(user_id="user_A")
    assert len(user_a_sessions) == 2
    assert set(s.session_id for s in user_a_sessions) == {s1.session_id, s3.session_id}

    manager.complete_session(s1.session_id)

    active_user_a = manager.list_active_sessions(user_id="user_A")
    assert len(active_user_a) == 1
    assert active_user_a[0].session_id == s3.session_id


def test_add_turn(manager: ConversationSessionManager) -> None:
    """Verifies adding a turn to an active session and enforcing turn immutability."""
    session = manager.create_session(user_id="user_123")

    turn = manager.add_turn(
        session_id=session.session_id,
        role="user",
        content="Hello Auralis",
        metadata={"intent": "greeting"},
    )

    assert turn is not None
    assert turn.role == "user"
    assert turn.content == "Hello Auralis"
    assert turn.metadata == {"intent": "greeting"}

    # Immutability check
    with pytest.raises((TypeError, ValidationError)):
        turn.content = "Modified content"


def test_ordering(manager: ConversationSessionManager) -> None:
    """Verifies turns are retrieved in strict chronological order."""
    session = manager.create_session(user_id="user_123")

    t1 = manager.add_turn(session.session_id, role="user", content="Turn 1")
    t2 = manager.add_turn(session.session_id, role="assistant", content="Turn 2")
    t3 = manager.add_turn(session.session_id, role="user", content="Turn 3")

    turns = manager.get_turns(session.session_id)
    assert len(turns) == 3
    assert [t.turn_id for t in turns] == [t1.turn_id, t2.turn_id, t3.turn_id]
    assert [t.content for t in turns] == ["Turn 1", "Turn 2", "Turn 3"]


def test_pause(manager: ConversationSessionManager) -> None:
    """Verifies pausing an active session."""
    session = manager.create_session(user_id="user_123")

    res = manager.pause_session(session.session_id)
    assert res is True

    updated = manager.get_session(session.session_id)
    assert updated.status == ConversationSessionStatus.PAUSED


def test_resume(manager: ConversationSessionManager) -> None:
    """Verifies resuming a paused session."""
    session = manager.create_session(user_id="user_123")
    manager.pause_session(session.session_id)

    res = manager.resume_session(session.session_id)
    assert res is True

    updated = manager.get_session(session.session_id)
    assert updated.status == ConversationSessionStatus.ACTIVE


def test_completion(manager: ConversationSessionManager) -> None:
    """Verifies completing a session and moving it to completed history."""
    session = manager.create_session(user_id="user_123")

    res = manager.complete_session(session.session_id)
    assert res is True

    updated = manager.get_session(session.session_id)
    assert updated.status == ConversationSessionStatus.COMPLETED

    active_list = manager.list_active_sessions()
    assert len(active_list) == 0


def test_cancellation(manager: ConversationSessionManager) -> None:
    """Verifies cancelling a session and moving it to history."""
    session = manager.create_session(user_id="user_123")

    res = manager.cancel_session(session.session_id)
    assert res is True

    updated = manager.get_session(session.session_id)
    assert updated.status == ConversationSessionStatus.CANCELLED


def test_expiration(manager: ConversationSessionManager) -> None:
    """Verifies automatic session expiration based on timeout."""
    session = manager.create_session(user_id="user_123")

    # Manually backdate last_activity to simulate timeout
    session.last_activity = datetime.now(timezone.utc) - timedelta(seconds=7200)

    expired = manager.expire_sessions(timeout_seconds=3600)
    assert session.session_id in expired

    updated = manager.get_session(session.session_id)
    assert updated.status == ConversationSessionStatus.EXPIRED


def test_removal(manager: ConversationSessionManager) -> None:
    """Verifies removal of active or historical sessions."""
    session = manager.create_session(user_id="user_123")

    removed = manager.remove_session(session.session_id)
    assert removed is True
    assert manager.get_session(session.session_id) is None


def test_history(manager: ConversationSessionManager) -> None:
    """Verifies completed history capacity enforcement limit."""
    cfg = ConversationSessionConfig(history_limit=2)
    mgr = ConversationSessionManager(config=cfg)

    s1 = mgr.create_session(user_id="u1")
    s2 = mgr.create_session(user_id="u2")
    s3 = mgr.create_session(user_id="u3")

    mgr.complete_session(s1.session_id)
    mgr.complete_session(s2.session_id)
    mgr.complete_session(s3.session_id)

    # s1 should have been purged due to history_limit=2
    assert mgr.get_session(s1.session_id) is None
    assert mgr.get_session(s2.session_id) is not None
    assert mgr.get_session(s3.session_id) is not None


def test_timestamps(manager: ConversationSessionManager) -> None:
    """Verifies created_at, updated_at, and last_activity update behavior."""
    session = manager.create_session(user_id="u1")
    initial_updated = session.updated_at

    turn = manager.add_turn(session.session_id, role="user", content="Check time")
    assert turn is not None
    assert session.updated_at >= initial_updated
    assert session.last_activity >= initial_updated


def test_metadata(manager: ConversationSessionManager) -> None:
    """Verifies metadata handling for sessions and turns."""
    session = manager.create_session(
        user_id="u1",
        metadata={"client": "desktop_app", "version": "1.0.0"},
    )
    turn = manager.add_turn(
        session.session_id,
        role="user",
        content="Hello",
        metadata={"tokens": 12},
    )

    assert session.metadata["client"] == "desktop_app"
    assert turn.metadata["tokens"] == 12


def test_dependency_injection() -> None:
    """Verifies manager honors custom ConversationSessionConfig dependency injection."""
    custom_cfg = ConversationSessionConfig(
        maximum_sessions=2,
        maximum_turns_per_session=3,
        session_timeout_seconds=60,
        history_limit=10,
    )
    mgr = ConversationSessionManager(config=custom_cfg)

    s1 = mgr.create_session(user_id="u1")
    mgr.add_turn(s1.session_id, "user", "T1")
    mgr.add_turn(s1.session_id, "user", "T2")
    mgr.add_turn(s1.session_id, "user", "T3")

    # 4th turn exceeds maximum_turns_per_session=3
    t4 = mgr.add_turn(s1.session_id, "user", "T4")
    assert t4 is None

    # Adding sessions exceeding maximum_sessions=2
    mgr.create_session(user_id="u2")
    mgr.create_session(user_id="u3")
    assert len(mgr.list_active_sessions()) <= 2


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent turn additions across multiple threads."""
    mgr = ConversationSessionManager()
    session = mgr.create_session(user_id="u1")

    def add_turn_worker(idx: int) -> None:
        mgr.add_turn(
            session_id=session.session_id,
            role="user",
            content=f"Concurrent content {idx}",
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(add_turn_worker, i) for i in range(50)]
        for f in futures:
            f.result()

    turns = mgr.get_turns(session.session_id)
    assert len(turns) == 50


def test_unknown_ids(manager: ConversationSessionManager) -> None:
    """Verifies that unknown IDs gracefully return None/False without throwing exceptions."""
    non_existent = "session_unknown_999"

    assert manager.get_session(non_existent) is None
    assert manager.get_turns(non_existent) == []
    assert manager.add_turn(non_existent, role="user", content="hi") is None
    assert manager.pause_session(non_existent) is False
    assert manager.resume_session(non_existent) is False
    assert manager.complete_session(non_existent) is False
    assert manager.cancel_session(non_existent) is False
    assert manager.remove_session(non_existent) is False
