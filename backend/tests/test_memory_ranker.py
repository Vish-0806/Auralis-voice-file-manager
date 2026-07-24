"""Unit tests for the MemoryRanker and its integration with ContextBuilder."""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from memory import (
    MemoryService,
    MemoryEntry,
    MemoryMetadata,
    MemoryType,
    ContextBuilder,
    MemoryRanker,
    MemoryRankerConfig,
)


@pytest.fixture
def mock_in_memory_service(monkeypatch):
    """Provides a MemoryService forced to use InMemoryProvider."""
    from memory.config import settings
    monkeypatch.setattr(settings, "provider_type", "in_memory")
    return MemoryService()


def test_ranker_scoring_calculation() -> None:
    """Verify that different criteria (session, workspace, entity, command) increase the relevance score."""
    ranker = MemoryRanker()
    now = datetime.now(timezone.utc)

    # 1. Base entry (recency only, created 1 hour ago)
    base_entry = MemoryEntry(
        id="base",
        content="some random description",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(hours=1))
    )

    # 2. Entry matching session
    session_entry = MemoryEntry(
        id="session",
        content="some random description",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(
            created_at=now - timedelta(hours=1),
            additional_info={"session_id": "current_sess"}
        )
    )

    # 3. Entry matching workspace path
    workspace_entry = MemoryEntry(
        id="workspace",
        content="C:\\workspace",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(
            created_at=now - timedelta(hours=1),
            additional_info={"workspace_path": "C:\\workspace"}
        )
    )

    # 4. Entry matching command keywords
    command_entry = MemoryEntry(
        id="command",
        content="please open chrome web browser",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(hours=1))
    )

    base_score = ranker.score_entry(base_entry)
    session_score = ranker.score_entry(session_entry, session_id="current_sess")
    workspace_score = ranker.score_entry(workspace_entry, workspace_path="C:\\workspace")
    command_score = ranker.score_entry(command_entry, query_text="open app")

    assert session_score > base_score
    assert workspace_score > base_score
    assert command_score > base_score


def test_ranker_config_overrides() -> None:
    """Verify that overriding weights in MemoryRankerConfig adjusts the calculated scores."""
    custom_config = MemoryRankerConfig(
        recency_weight=0.0,
        session_weight=1.0,
        workspace_weight=0.0,
        entity_weight=0.0,
        command_weight=0.0,
    )
    ranker = MemoryRanker(config=custom_config)
    now = datetime.now(timezone.utc)

    matching_entry = MemoryEntry(
        id="match",
        content="hello world",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(
            created_at=now - timedelta(days=10),
            additional_info={"session_id": "sess_x"}
        )
    )

    score = ranker.score_entry(matching_entry, session_id="sess_x")
    # Score should be exactly 1.0 because session matches and session weight is 1.0 (others are 0.0)
    assert abs(score - 1.0) < 1e-5


@pytest.mark.anyio
async def test_ranker_context_builder_integration(mock_in_memory_service) -> None:
    """Verify ContextBuilder invokes the ranker and honors the configured limits."""
    service = mock_in_memory_service
    unique = "_lim"

    # Seed 6 conversation entries (limit is 5 by default in MemoryRankerConfig)
    for i in range(6):
        await service.save(MemoryEntry(
            id=f"conv_{i}{unique}",
            content=f"conversation message {i}",
            memory_type=MemoryType.CONVERSATION,
            metadata=MemoryMetadata(additional_info={"user_id": 123})
        ))

    # Initialize ContextBuilder with standard config
    config = MemoryRankerConfig(max_conversations=3)
    builder = ContextBuilder(service, ranker_config=config)

    context = await builder.build_context(user_id=123)

    # Max conversations slice limit of 3 should be respected
    assert len(context.recent_conversations) == 3


def test_normalize_token() -> None:
    """Verify lowercasing and punctuation stripping functionality."""
    ranker = MemoryRanker()
    assert ranker._normalize_token("Create,") == "create"
    assert ranker._normalize_token("Launch!") == "launch"
    assert ranker._normalize_token("Organize...") == "organize"
    assert ranker._normalize_token("...Delete...") == "delete"
    assert ranker._normalize_token("") == ""


def test_score_importance() -> None:
    """Verify that type-based importance scoring returns configured values."""
    custom_config = MemoryRankerConfig(
        recency_weight=0.0,
        session_weight=0.0,
        workspace_weight=0.0,
        entity_weight=0.0,
        command_weight=0.0,
        importance_weight=1.0,
        importance_weights={"session": 1.0, "conversation": 0.5}
    )
    ranker = MemoryRanker(config=custom_config)

    session_entry = MemoryEntry(
        id="session",
        content="session ctx",
        memory_type=MemoryType.SESSION
    )
    conv_entry = MemoryEntry(
        id="conv",
        content="conv text",
        memory_type=MemoryType.CONVERSATION
    )

    assert ranker._score_importance(session_entry) == 1.0
    assert ranker._score_importance(conv_entry) == 0.5

    # Check overall score calculation
    assert abs(ranker.score_entry(session_entry) - 1.0) < 1e-5
    assert abs(ranker.score_entry(conv_entry) - 0.5) < 1e-5


def test_score_frequency() -> None:
    """Verify that BM25-style frequency scoring functions as expected with a saturation curve."""
    custom_config = MemoryRankerConfig(
        recency_weight=0.0,
        session_weight=0.0,
        workspace_weight=0.0,
        entity_weight=0.0,
        command_weight=0.0,
        frequency_weight=1.0,
        frequency_k=5.0
    )
    ranker = MemoryRanker(config=custom_config)

    entry_none = MemoryEntry(
        id="none",
        content="no usage",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(additional_info={})
    )
    entry_5 = MemoryEntry(
        id="five",
        content="five usages",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(additional_info={"usage_count": 5})
    )
    entry_invalid = MemoryEntry(
        id="invalid",
        content="invalid usage",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(additional_info={"usage_count": "invalid"})
    )

    assert ranker._score_frequency(entry_none) == 0.0
    assert ranker._score_frequency(entry_5) == 5.0 / (5.0 + 5.0)  # 0.5
    assert ranker._score_frequency(entry_invalid) == 0.0

    assert abs(ranker.score_entry(entry_5) - 0.5) < 1e-5


def test_synonym_mappings() -> None:
    """Verify command synonyms are mapped to canonical forms and correctly matched."""
    custom_config = MemoryRankerConfig(
        recency_weight=0.0,
        session_weight=0.0,
        workspace_weight=0.0,
        entity_weight=0.0,
        command_weight=1.0,
    )
    ranker = MemoryRanker(config=custom_config)

    entry_del = MemoryEntry(
        id="del",
        content="delete the voice recording",
        memory_type=MemoryType.CONVERSATION
    )

    score_remove = ranker.score_entry(entry_del, query_text="remove app")
    score_erase = ranker.score_entry(entry_del, query_text="erase file")
    score_unrelated = ranker.score_entry(entry_del, query_text="hello world")

    assert score_remove == 1.0
    assert score_erase == 1.0
    assert score_unrelated == 0.0


def test_helper_methods_direct_calls() -> None:
    """Verify direct calls to all individual private scoring helper methods."""
    ranker = MemoryRanker()
    now = datetime.now(timezone.utc)
    entry = MemoryEntry(
        id="test_all",
        content="some project path",
        memory_type=MemoryType.PROJECT,
        metadata=MemoryMetadata(
            created_at=now,
            additional_info={"session_id": "sess_123", "workspace_path": "some path", "usage_count": 10}
        )
    )

    assert ranker._score_recency(entry) > 0.99
    assert ranker._score_session(entry, "sess_123") == 1.0
    assert ranker._score_session(entry, "other_sess") == 0.0
    assert ranker._score_workspace(entry, "some path") == 1.0
    assert ranker._score_workspace(entry, "other path") == 0.0
    assert ranker._score_entity_similarity(entry, "project path query") == 2/3
    assert ranker._score_importance(entry) == 0.8
    assert ranker._score_frequency(entry) == 10.0 / (10.0 + 5.0)
