"""Unit tests for ConversationReferenceResolver (Phase 9.1.3)."""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.conversation.reference_resolver import (
    ConversationReferenceResolver,
    ReferenceCandidate,
    ReferenceResolutionResult,
    ReferenceResolverConfig,
    ReferenceType,
)


@pytest.fixture
def resolver() -> ConversationReferenceResolver:
    """Fixture providing a fresh ConversationReferenceResolver instance."""
    return ConversationReferenceResolver()


def test_entity_registration(resolver: ConversationReferenceResolver) -> None:
    """Verifies registering a single entity candidate."""
    cand = resolver.register_entity(
        candidate_or_id="file_report_pdf",
        display_name="Q3 Financial Report.pdf",
        reference_type=ReferenceType.ENTITY,
        metadata={"path": "/docs/report.pdf"},
    )

    assert cand.identifier == "file_report_pdf"
    assert cand.display_name == "Q3 Financial Report.pdf"
    assert cand.reference_type == ReferenceType.ENTITY

    entities = resolver.list_entities()
    assert len(entities) == 1
    assert entities[0].identifier == "file_report_pdf"


def test_multiple_registrations(resolver: ConversationReferenceResolver) -> None:
    """Verifies batch registration of entities."""
    c1 = ReferenceCandidate(identifier="id1", display_name="Doc 1")
    c2 = ReferenceCandidate(identifier="id2", display_name="Doc 2")

    resolver.register_entities([c1, c2])
    entities = resolver.list_entities()
    assert len(entities) == 2
    assert [e.identifier for e in entities] == ["id1", "id2"]


def test_history_trimming() -> None:
    """Verifies maximum_reference_history capacity bound trimming."""
    cfg = ReferenceResolverConfig(maximum_reference_history=3)
    res = ConversationReferenceResolver(config=cfg)

    for i in range(5):
        res.register_entity(f"id_{i}", display_name=f"Name {i}")

    entities = res.list_entities()
    assert len(entities) == 3
    assert [e.identifier for e in entities] == ["id_2", "id_3", "id_4"]


def test_pronoun_resolution(resolver: ConversationReferenceResolver) -> None:
    """Verifies pronoun resolution (it, that, this, them)."""
    resolver.register_entity("file_a", display_name="File A.txt")
    resolver.register_entity("file_b", display_name="File B.txt")

    # 'it' should resolve to most recently registered entity ('file_b')
    res_it = resolver.resolve_reference("it")
    assert res_it.resolved is True
    assert res_it.candidate.identifier == "file_b"

    res_that = resolver.resolve_pronoun("that")
    assert res_that.resolved is True
    assert res_that.candidate.identifier == "file_b"


def test_ordinal_resolution(resolver: ConversationReferenceResolver) -> None:
    """Verifies ordinal resolution (first, second, third, 1st, last)."""
    resolver.register_entity("e1", display_name="Item 1")
    resolver.register_entity("e2", display_name="Item 2")
    resolver.register_entity("e3", display_name="Item 3")

    res_first = resolver.resolve_reference("first")
    assert res_first.resolved is True
    assert res_first.candidate.identifier == "e1"

    res_2nd = resolver.resolve_reference("2nd")
    assert res_2nd.resolved is True
    assert res_2nd.candidate.identifier == "e2"

    res_last = resolver.resolve_reference("last")
    assert res_last.resolved is True
    assert res_last.candidate.identifier == "e3"


def test_temporal_resolution(resolver: ConversationReferenceResolver) -> None:
    """Verifies temporal resolution (latest, previous, earlier, recent)."""
    resolver.register_entity("e1", display_name="Old Doc")
    resolver.register_entity("e2", display_name="New Doc")

    res_latest = resolver.resolve_temporal("latest")
    assert res_latest.resolved is True
    assert res_latest.candidate.identifier == "e2"

    res_prev = resolver.resolve_temporal("previous")
    assert res_prev.resolved is True
    assert res_prev.candidate.identifier == "e1"


def test_relative_resolution(resolver: ConversationReferenceResolver) -> None:
    """Verifies relative resolution (next, before, after)."""
    resolver.register_entity("e1", display_name="Doc 1")
    resolver.register_entity("e2", display_name="Doc 2")

    res_next = resolver.resolve_relative("next")
    assert res_next.resolved is True
    assert res_next.candidate.identifier == "e2"

    res_before = resolver.resolve_relative("before")
    assert res_before.resolved is True
    assert res_before.candidate.identifier == "e1"


def test_confidence_values() -> None:
    """Verifies minimum_confidence filtering in ReferenceResolverConfig."""
    cfg = ReferenceResolverConfig(minimum_confidence=0.90)
    res = ConversationReferenceResolver(config=cfg)

    # Register candidate with low confidence
    cand = ReferenceCandidate(identifier="low_conf", display_name="Low", confidence=0.40)
    res.register_entity(cand)

    result = res.resolve_reference("it")
    assert result.resolved is False


def test_unresolved_references(resolver: ConversationReferenceResolver) -> None:
    """Verifies unresolved returns on empty history or unknown text."""
    res_empty = resolver.resolve_reference("it")
    assert res_empty.resolved is False
    assert res_empty.candidate is None

    resolver.register_entity("e1", display_name="Doc 1")
    res_unknown = resolver.resolve_reference("nonexistent_random_xyz")
    assert res_unknown.resolved is False


def test_immutable_models() -> None:
    """Verifies immutability of ReferenceCandidate and ReferenceResolutionResult."""
    cand = ReferenceCandidate(identifier="id1", display_name="Doc 1")
    with pytest.raises((TypeError, ValidationError)):
        cand.display_name = "Modified"

    res = ReferenceResolutionResult(reference="it", resolved=False)
    with pytest.raises((TypeError, ValidationError)):
        res.resolved = True


def test_entity_removal(resolver: ConversationReferenceResolver) -> None:
    """Verifies entity removal by identifier."""
    resolver.register_entity("e1", display_name="Doc 1")
    resolver.register_entity("e2", display_name="Doc 2")

    removed = resolver.remove_entity("e1")
    assert removed is True

    entities = resolver.list_entities()
    assert len(entities) == 1
    assert entities[0].identifier == "e2"


def test_clearing_history(resolver: ConversationReferenceResolver) -> None:
    """Verifies clear_history clears entity storage."""
    resolver.register_entity("e1", display_name="Doc 1")
    resolver.clear_history()

    assert resolver.list_entities() == []


def test_list_entities(resolver: ConversationReferenceResolver) -> None:
    """Verifies list_entities returns chronological entity list."""
    resolver.register_entity("e1", display_name="Doc 1")
    resolver.register_entity("e2", display_name="Doc 2")

    entities = resolver.list_entities()
    assert [e.identifier for e in entities] == ["e1", "e2"]


def test_duplicate_entities(resolver: ConversationReferenceResolver) -> None:
    """Verifies re-registering an entity updates its position to most recent."""
    resolver.register_entity("e1", display_name="Doc 1")
    resolver.register_entity("e2", display_name="Doc 2")
    resolver.register_entity("e1", display_name="Doc 1 Re-registered")

    entities = resolver.list_entities()
    assert len(entities) == 2
    assert [e.identifier for e in entities] == ["e2", "e1"]
    assert entities[1].display_name == "Doc 1 Re-registered"


def test_metadata(resolver: ConversationReferenceResolver) -> None:
    """Verifies metadata propagation in candidates."""
    cand = resolver.register_entity(
        "e1", display_name="Doc 1", metadata={"type": "pdf", "size": 1024}
    )
    assert cand.metadata["type"] == "pdf"


def test_dependency_injection() -> None:
    """Verifies dependency injection of custom ReferenceResolverConfig."""
    custom_cfg = ReferenceResolverConfig(minimum_confidence=0.80, maximum_reference_history=2)
    res = ConversationReferenceResolver(config=custom_cfg)

    res.register_entity("e1", display_name="D1")
    res.register_entity("e2", display_name="D2")
    res.register_entity("e3", display_name="D3")

    assert len(res.list_entities()) == 2


def test_thread_safety() -> None:
    """Verifies thread safety under concurrent entity registrations and resolutions."""
    res = ConversationReferenceResolver()

    def register_worker(idx: int) -> None:
        res.register_entity(f"id_{idx}", display_name=f"Doc {idx}")
        res.resolve_reference("it")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_worker, i) for i in range(50)]
        for f in futures:
            f.result()

    assert len(res.list_entities()) == 50


def test_invalid_references(resolver: ConversationReferenceResolver) -> None:
    """Verifies graceful handling of empty or whitespace reference strings."""
    res_none = resolver.resolve_reference("")
    assert res_none.resolved is False

    res_space = resolver.resolve_reference("   ")
    assert res_space.resolved is False


def test_maximum_history(resolver: ConversationReferenceResolver) -> None:
    """Verifies default maximum_reference_history (100) bound."""
    for i in range(150):
        resolver.register_entity(f"id_{i}", display_name=f"Doc {i}")

    entities = resolver.list_entities()
    assert len(entities) == 100
    assert entities[0].identifier == "id_50"
    assert entities[-1].identifier == "id_149"


def test_graceful_failure(resolver: ConversationReferenceResolver) -> None:
    """Verifies invalid queries return unresolved result without throwing uncaught exceptions."""
    result = resolver.resolve_reference("invalid_query_that_matches_nothing")
    assert isinstance(result, ReferenceResolutionResult)
    assert result.resolved is False
    assert result.candidate is None
