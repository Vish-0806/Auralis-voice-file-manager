"""Unit tests for ConversationSummarizer (Phase 9.1.4)."""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.conversation.conversation_session import ConversationTurn
from brain.conversation.summarizer import (
    ConversationSummarizer,
    ConversationSummary,
    ConversationSummaryConfig,
)


@pytest.fixture
def summarizer() -> ConversationSummarizer:
    """Fixture providing a fresh ConversationSummarizer instance."""
    return ConversationSummarizer()


def test_create_summary(summarizer: ConversationSummarizer) -> None:
    """Verifies creating a structured summary from turns."""
    turns = [
        ConversationTurn(turn_id="t1", role="user", content='Please move "report.pdf" to Downloads', metadata={"filename": "report.pdf", "action": "move file"}),
        ConversationTurn(turn_id="t2", role="assistant", content="Destination folder selected. Awaiting user confirmation", metadata={"decision": "destination folder selected", "open_item": "awaiting user confirmation"}),
    ]

    summary = summarizer.create_summary(session_id="session_101", turns=turns)

    assert summary.session_id == "session_101"
    assert summary.covered_turns == 2
    assert "report.pdf" in summary.key_entities
    assert "move file" in summary.key_topics
    assert "destination folder selected" in summary.decisions
    assert "awaiting user confirmation" in summary.open_items
    assert isinstance(summary.created_at, datetime)
    assert isinstance(summary.updated_at, datetime)


def test_retrieve_summary(summarizer: ConversationSummarizer) -> None:
    """Verifies retrieving summary by session ID or summary ID."""
    turns = [ConversationTurn(turn_id="t1", role="user", content="Hello")]
    created = summarizer.create_summary(session_id="session_101", turns=turns)

    retrieved = summarizer.get_summary("session_101")
    assert retrieved is not None
    assert retrieved.summary_id == created.summary_id

    by_id = summarizer.get_summary("session_101", summary_id=created.summary_id)
    assert by_id is not None
    assert by_id.summary_id == created.summary_id


def test_update_summary(summarizer: ConversationSummarizer) -> None:
    """Verifies incrementally updating an existing summary with new turns."""
    turns1 = [ConversationTurn(turn_id="t1", role="user", content='Move "file_a.txt"', metadata={"entity": "file_a.txt"})]
    initial = summarizer.create_summary("session_101", turns=turns1)

    turns2 = [ConversationTurn(turn_id="t2", role="user", content='Move "file_b.txt"', metadata={"entity": "file_b.txt"})]
    updated = summarizer.update_summary("session_101", new_turns=turns2)

    assert updated is not None
    assert updated.covered_turns == 2
    assert "file_a.txt" in updated.key_entities
    assert "file_b.txt" in updated.key_entities


def test_merge_summaries(summarizer: ConversationSummarizer) -> None:
    """Verifies merging two summaries into a higher-level summary."""
    t1 = [ConversationTurn(turn_id="t1", role="user", content="Task 1", metadata={"entity": "Ent1", "topic": "Top1"})]
    t2 = [ConversationTurn(turn_id="t2", role="user", content="Task 2", metadata={"entity": "Ent2", "topic": "Top2"})]

    s1 = summarizer.summarize_turns("session_101", t1, summary_level=1)
    s2 = summarizer.summarize_turns("session_101", t2, summary_level=1)

    merged = summarizer.merge_summaries(s1, s2)
    assert merged.summary_level == 2
    assert merged.covered_turns == 2
    assert "Ent1" in merged.key_entities and "Ent2" in merged.key_entities
    assert "Top1" in merged.key_topics and "Top2" in merged.key_topics


def test_chronological_preservation(summarizer: ConversationSummarizer) -> None:
    """Verifies chronological order of items is preserved during extraction."""
    turns = [
        ConversationTurn(turn_id="t1", role="user", content="Alpha", metadata={"entities": ["Alpha", "Beta"]}),
        ConversationTurn(turn_id="t2", role="user", content="Gamma", metadata={"entities": ["Gamma", "Alpha"]}),
    ]

    summary = summarizer.summarize_turns("s1", turns)
    assert summary.key_entities == ["Alpha", "Beta", "Gamma"]


def test_entity_extraction(summarizer: ConversationSummarizer) -> None:
    """Verifies entity extraction from turn metadata and quoted content."""
    turns = [
        ConversationTurn(turn_id="t1", role="user", content='Open "document.docx"', metadata={"filename": "document.docx"}),
    ]
    summary = summarizer.summarize_turns("s1", turns)
    assert "document.docx" in summary.key_entities


def test_topic_extraction(summarizer: ConversationSummarizer) -> None:
    """Verifies topic extraction from metadata and action keywords."""
    turns = [
        ConversationTurn(turn_id="t1", role="user", content="Please rename folder now", metadata={"intent": "rename folder"}),
    ]
    summary = summarizer.summarize_turns("s1", turns)
    assert "rename folder" in summary.key_topics


def test_decision_extraction(summarizer: ConversationSummarizer) -> None:
    """Verifies decision extraction from metadata and decision text."""
    turns = [
        ConversationTurn(turn_id="t1", role="assistant", content="Destination folder selected", metadata={"decision": "destination folder selected"}),
    ]
    summary = summarizer.summarize_turns("s1", turns)
    assert "destination folder selected" in summary.decisions


def test_open_item_extraction(summarizer: ConversationSummarizer) -> None:
    """Verifies open item extraction from metadata and query text."""
    turns = [
        ConversationTurn(turn_id="t1", role="assistant", content="Awaiting user confirmation to proceed", metadata={"open_item": "awaiting user confirmation"}),
    ]
    summary = summarizer.summarize_turns("s1", turns)
    assert "awaiting user confirmation" in summary.open_items


def test_duplicate_elimination(summarizer: ConversationSummarizer) -> None:
    """Verifies duplicate entities and topics are deduplicated."""
    turns = [
        ConversationTurn(turn_id="t1", role="user", content="E1 E1", metadata={"entities": ["E1", "E1"]}),
        ConversationTurn(turn_id="t2", role="user", content="E1", metadata={"entity": "E1"}),
    ]
    summary = summarizer.summarize_turns("s1", turns)
    assert summary.key_entities == ["E1"]


def test_immutable_models() -> None:
    """Verifies ConversationSummary is immutable snapshot model."""
    summary = ConversationSummary(summary_id="s1", session_id="sess1")
    with pytest.raises((TypeError, ValidationError)):
        summary.covered_turns = 10


def test_metadata(summarizer: ConversationSummarizer) -> None:
    """Verifies summary metadata handling and preservation."""
    turns = [ConversationTurn(turn_id="t1", role="user", content="Hi")]
    summary = summarizer.create_summary("s1", turns, metadata={"source": "test"})
    assert summary.metadata == {"source": "test"}


def test_timestamps(summarizer: ConversationSummarizer) -> None:
    """Verifies timestamps created_at and updated_at on creation and update."""
    turns1 = [ConversationTurn(turn_id="t1", role="user", content="Hi")]
    created = summarizer.create_summary("s1", turns1)

    turns2 = [ConversationTurn(turn_id="t2", role="user", content="Bye")]
    updated = summarizer.update_summary("s1", turns2)

    assert updated.updated_at >= created.updated_at
    assert updated.created_at == created.created_at


def test_removal(summarizer: ConversationSummarizer) -> None:
    """Verifies summary removal by summary ID."""
    turns = [ConversationTurn(turn_id="t1", role="user", content="Hi")]
    summary = summarizer.create_summary("s1", turns)

    removed = summarizer.remove_summary(summary.summary_id)
    assert removed is True
    assert summarizer.get_summary("s1") is None


def test_clearing(summarizer: ConversationSummarizer) -> None:
    """Verifies clear removes all summaries."""
    turns = [ConversationTurn(turn_id="t1", role="user", content="Hi")]
    summarizer.create_summary("s1", turns)
    summarizer.clear()

    assert summarizer.list_summaries() == []


def test_listing(summarizer: ConversationSummarizer) -> None:
    """Verifies list_summaries for all or session-filtered summaries."""
    t = [ConversationTurn(turn_id="t1", role="user", content="Hi")]
    s1 = summarizer.create_summary("sess_A", t)
    s2 = summarizer.create_summary("sess_B", t)

    all_s = summarizer.list_summaries()
    assert len(all_s) == 2

    filtered = summarizer.list_summaries("sess_A")
    assert len(filtered) == 1
    assert filtered[0].summary_id == s1.summary_id


def test_dependency_injection() -> None:
    """Verifies custom ConversationSummaryConfig dependency injection."""
    custom_cfg = ConversationSummaryConfig(maximum_entities=2)
    summr = ConversationSummarizer(config=custom_cfg)

    turns = [ConversationTurn(turn_id="t1", role="user", content="E1 E2 E3", metadata={"entities": ["E1", "E2", "E3"]})]
    summary = summr.summarize_turns("s1", turns)
    assert len(summary.key_entities) == 2


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent summary creations and updates."""
    summr = ConversationSummarizer()
    t = [ConversationTurn(turn_id="t1", role="user", content="Hi", metadata={"entity": "file.txt"})]
    summr.create_summary("s1", t)

    def update_worker(idx: int) -> None:
        turns = [ConversationTurn(turn_id=f"t_{idx}", role="user", content=f"Msg {idx}", metadata={"entity": f"file_{idx}.txt"})]
        summr.update_summary("s1", new_turns=turns)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(update_worker, i) for i in range(50)]
        for f in futures:
            f.result()

    updated = summr.get_summary("s1")
    assert updated.covered_turns == 51


def test_invalid_session_ids(summarizer: ConversationSummarizer) -> None:
    """Verifies unknown session IDs return None gracefully without throwing exceptions."""
    non_existent = "session_unknown_999"

    assert summarizer.get_summary(non_existent) is None
    assert summarizer.update_summary(non_existent, new_turns=[]) is None
    assert summarizer.remove_summary("non_existent_summary_id") is False


def test_configuration_limits() -> None:
    """Verifies maximum entity/topic limits in config are respected."""
    cfg = ConversationSummaryConfig(maximum_topics=1)
    summr = ConversationSummarizer(config=cfg)

    turns = [ConversationTurn(turn_id="t1", role="user", content="Hi", metadata={"topics": ["TopicA", "TopicB"]})]
    summary = summr.summarize_turns("s1", turns)
    assert len(summary.key_topics) == 1


def test_incremental_updates(summarizer: ConversationSummarizer) -> None:
    """Verifies incremental update never loses pre-existing summary data."""
    t1 = [ConversationTurn(turn_id="t1", role="user", content="Hi", metadata={"entity": "A", "topic": "T1"})]
    summary1 = summarizer.create_summary("s1", t1)

    t2 = [ConversationTurn(turn_id="t2", role="user", content="Bye", metadata={"entity": "B", "topic": "T2"})]
    summary2 = summarizer.update_summary("s1", t2)

    assert "A" in summary2.key_entities and "B" in summary2.key_entities
    assert "T1" in summary2.key_topics and "T2" in summary2.key_topics


def test_graceful_failures(summarizer: ConversationSummarizer) -> None:
    """Verifies empty turn lists handle gracefully returning valid summary."""
    summary = summarizer.summarize_turns("s1", turns=[])
    assert summary.total_turns == 0
    assert summary.covered_turns == 0
    assert summary.key_entities == []
