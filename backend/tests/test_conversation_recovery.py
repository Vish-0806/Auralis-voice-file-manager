"""Unit tests for ConversationRecoveryManager (Phase 9.1.5)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.conversation.context_manager import ConversationContextManager
from brain.conversation.conversation_session import ConversationSessionManager, ConversationTurn
from brain.conversation.recovery import (
    ConversationRecoveryConfig,
    ConversationRecoveryManager,
    ConversationRecoveryRecord,
    ConversationRecoveryStatus,
)
from brain.conversation.summarizer import ConversationSummarizer


@pytest.fixture
def recovery_mgr() -> ConversationRecoveryManager:
    """Fixture providing a fresh ConversationRecoveryManager instance."""
    return ConversationRecoveryManager()


@pytest.fixture
def session_mgr() -> ConversationSessionManager:
    """Fixture providing a fresh ConversationSessionManager instance."""
    return ConversationSessionManager()


@pytest.fixture
def context_mgr() -> ConversationContextManager:
    """Fixture providing a fresh ConversationContextManager instance."""
    return ConversationContextManager()


@pytest.fixture
def summarizer() -> ConversationSummarizer:
    """Fixture providing a fresh ConversationSummarizer instance."""
    return ConversationSummarizer()


def test_create_recovery_record(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies creating a recovery tracking record."""
    rec = recovery_mgr.create_recovery_record(session_id="session_101", metadata={"origin": "crash"})

    assert rec.session_id == "session_101"
    assert rec.status == ConversationRecoveryStatus.PENDING
    assert rec.metadata == {"origin": "crash"}
    assert isinstance(rec.created_at, datetime)
    assert rec.recovered_at is None


def test_recover_session(
    recovery_mgr: ConversationRecoveryManager, session_mgr: ConversationSessionManager
) -> None:
    """Verifies session recovery from session manager."""
    session = session_mgr.create_session(user_id="u1", session_id="sess_101")
    rec = recovery_mgr.create_recovery_record(session_id="sess_101")

    recovered = recovery_mgr.recover_session("sess_101", session_manager=session_mgr)
    assert recovered is not None
    assert recovered.session_id == "sess_101"

    updated_rec = recovery_mgr.list_records(session_id="sess_101")[0]
    assert updated_rec.status == ConversationRecoveryStatus.RECOVERED
    assert isinstance(updated_rec.recovered_at, datetime)


def test_recover_context(
    recovery_mgr: ConversationRecoveryManager, context_mgr: ConversationContextManager
) -> None:
    """Verifies context recovery from context manager."""
    context_mgr.create_context(session_id="sess_101")
    ctx = recovery_mgr.recover_context("sess_101", context_manager=context_mgr)

    assert ctx is not None
    assert ctx.session_id == "sess_101"


def test_recover_summary(
    recovery_mgr: ConversationRecoveryManager, summarizer: ConversationSummarizer
) -> None:
    """Verifies summary recovery from summarizer."""
    turns = [ConversationTurn(turn_id="t1", role="user", content="Hi")]
    summarizer.create_summary(session_id="sess_101", turns=turns)

    summary = recovery_mgr.recover_summary("sess_101", summarizer=summarizer)
    assert summary is not None
    assert summary.session_id == "sess_101"


def test_recovered_status(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies marking a record as RECOVERED."""
    rec = recovery_mgr.create_recovery_record(session_id="sess_101")

    marked = recovery_mgr.mark_recovered(rec.recovery_id, reason="Manual recovery")
    assert marked is not None
    assert marked.status == ConversationRecoveryStatus.RECOVERED
    assert marked.reason == "Manual recovery"
    assert marked.recovered_at is not None


def test_failed_status(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies marking a record as FAILED."""
    rec = recovery_mgr.create_recovery_record(session_id="sess_101")

    marked = recovery_mgr.mark_failed(rec.recovery_id, reason="Corrupted payload")
    assert marked is not None
    assert marked.status == ConversationRecoveryStatus.FAILED
    assert marked.reason == "Corrupted payload"


def test_expired_status(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies marking a record as EXPIRED."""
    rec = recovery_mgr.create_recovery_record(session_id="sess_101")

    marked = recovery_mgr.mark_expired(rec.recovery_id, reason="Session timed out")
    assert marked is not None
    assert marked.status == ConversationRecoveryStatus.EXPIRED


def test_cleanup(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies cleanup of expired records."""
    rec = recovery_mgr.create_recovery_record("s1")
    # Backdate created_at to trigger expiration
    recovery_mgr._recovery_records[rec.recovery_id] = ConversationRecoveryRecord(
        recovery_id=rec.recovery_id,
        session_id=rec.session_id,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=7200),
        status=ConversationRecoveryStatus.PENDING,
    )

    removed = recovery_mgr.cleanup(timeout_seconds=3600)
    assert removed == 1
    assert recovery_mgr.list_records() == []


def test_retention_enforcement() -> None:
    """Verifies retention limit enforcement on cleanup."""
    cfg = ConversationRecoveryConfig(retention_limit=2)
    mgr = ConversationRecoveryManager(config=cfg)

    mgr.create_recovery_record("s1")
    mgr.create_recovery_record("s2")
    mgr.create_recovery_record("s3")

    mgr.cleanup()
    assert len(mgr.list_records()) <= 2


def test_timestamps(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies created_at and recovered_at timestamps."""
    rec = recovery_mgr.create_recovery_record("s1")
    assert rec.created_at is not None
    assert rec.recovered_at is None

    marked = recovery_mgr.mark_recovered(rec.recovery_id)
    assert marked.recovered_at >= rec.created_at


def test_metadata(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies recovery record metadata handling."""
    rec = recovery_mgr.create_recovery_record("s1", metadata={"retry_count": 2})
    assert rec.metadata == {"retry_count": 2}


def test_immutable_models() -> None:
    """Verifies ConversationRecoveryRecord immutability."""
    rec = ConversationRecoveryRecord(recovery_id="r1", session_id="s1")
    with pytest.raises((TypeError, ValidationError)):
        rec.status = ConversationRecoveryStatus.RECOVERED


def test_dependency_injection() -> None:
    """Verifies dependency injection of custom ConversationRecoveryConfig."""
    cfg = ConversationRecoveryConfig(
        maximum_recovery_records=2,
        recovery_timeout_seconds=60,
        retention_limit=2,
        automatic_cleanup=False,
    )
    mgr = ConversationRecoveryManager(config=cfg)

    mgr.create_recovery_record("s1")
    mgr.create_recovery_record("s2")
    mgr.create_recovery_record("s3")

    assert len(mgr._recovery_records) <= 2


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent record creation and status updates."""
    mgr = ConversationRecoveryManager()

    def worker(idx: int) -> None:
        rec = mgr.create_recovery_record(f"s_{idx}")
        mgr.mark_recovered(rec.recovery_id)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    records = mgr.list_records()
    assert len(records) == 50


def test_invalid_ids(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies unknown IDs return None/False gracefully without throwing exceptions."""
    non_existent = "rec_unknown_999"

    assert recovery_mgr.mark_recovered(non_existent) is None
    assert recovery_mgr.mark_failed(non_existent) is None
    assert recovery_mgr.mark_expired(non_existent) is None
    assert recovery_mgr.remove_record(non_existent) is False


def test_removal(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies record removal by recovery_id."""
    rec = recovery_mgr.create_recovery_record("s1")

    removed = recovery_mgr.remove_record(rec.recovery_id)
    assert removed is True
    assert recovery_mgr.list_records() == []


def test_listing(recovery_mgr: ConversationRecoveryManager) -> None:
    """Verifies list_records with session_id and status filtering."""
    r1 = recovery_mgr.create_recovery_record("s1")
    r2 = recovery_mgr.create_recovery_record("s2")

    recovery_mgr.mark_recovered(r1.recovery_id)

    recovered_list = recovery_mgr.list_records(status=ConversationRecoveryStatus.RECOVERED)
    assert len(recovered_list) == 1
    assert recovered_list[0].recovery_id == r1.recovery_id

    s2_list = recovery_mgr.list_records(session_id="s2")
    assert len(s2_list) == 1
    assert s2_list[0].recovery_id == r2.recovery_id


def test_automatic_cleanup() -> None:
    """Verifies automatic cleanup on list_records when automatic_cleanup=True."""
    cfg = ConversationRecoveryConfig(automatic_cleanup=True, recovery_timeout_seconds=10)
    mgr = ConversationRecoveryManager(config=cfg)

    rec = mgr.create_recovery_record("s1")
    mgr._recovery_records[rec.recovery_id] = ConversationRecoveryRecord(
        recovery_id=rec.recovery_id,
        session_id=rec.session_id,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=20),
        status=ConversationRecoveryStatus.PENDING,
    )

    records = mgr.list_records()
    assert len(records) == 0


def test_graceful_failures(
    recovery_mgr: ConversationRecoveryManager, session_mgr: ConversationSessionManager
) -> None:
    """Verifies recover_session marks PENDING record FAILED when session is missing."""
    recovery_mgr.create_recovery_record("non_existent_session")

    recovered = recovery_mgr.recover_session("non_existent_session", session_manager=session_mgr)
    assert recovered is None

    records = recovery_mgr.list_records(session_id="non_existent_session")
    assert len(records) == 1
    assert records[0].status == ConversationRecoveryStatus.FAILED


def test_recovery_timeout() -> None:
    """Verifies recovery timeout config behavior."""
    cfg = ConversationRecoveryConfig(recovery_timeout_seconds=30)
    mgr = ConversationRecoveryManager(config=cfg)

    rec = mgr.create_recovery_record("s1")
    mgr._recovery_records[rec.recovery_id] = ConversationRecoveryRecord(
        recovery_id=rec.recovery_id,
        session_id=rec.session_id,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=40),
        status=ConversationRecoveryStatus.PENDING,
    )

    removed = mgr.cleanup()
    assert removed == 1


def test_retention_limit() -> None:
    """Verifies maximum recovery record capacity bound."""
    cfg = ConversationRecoveryConfig(maximum_recovery_records=3)
    mgr = ConversationRecoveryManager(config=cfg)

    for i in range(5):
        mgr.create_recovery_record(f"s_{i}")

    assert len(mgr.list_records()) <= 3


def test_configuration_validation() -> None:
    """Verifies configuration options defaults."""
    cfg = ConversationRecoveryConfig()
    assert cfg.maximum_recovery_records == 1000
    assert cfg.recovery_timeout_seconds == 3600
    assert cfg.retention_limit == 5000
    assert cfg.automatic_cleanup is True
