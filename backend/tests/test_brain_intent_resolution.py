"""Unit test suite for Phase 12.2 — Intent Resolution Engine.

Covers:
- Intent models, enums, and immutability
- Subsystem exceptions hierarchy
- Text normalization, filler removal, command detection, and confidence scoring
- Entity extraction (files, folders, paths, apps, numbers, dates, times, devices)
- Resolution candidate scoring, context merging, and ambiguity handling
- Intent validation and dangerous request detection
- IntentProvider end-to-end processing and statistics
- IntentRuntime lifecycle, health checks, singleton identity, and thread safety
- Edge cases (empty input, whitespace, invalid input, multiple commands, conflicting entities)
"""

from concurrent.futures import ThreadPoolExecutor
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.intent import (
    AmbiguityLevel,
    AmbiguousIntentError,
    EntityExtractionError,
    EntityExtractor,
    EntityType,
    IntentCandidate,
    IntentCategory,
    IntentConfidence,
    IntentContext,
    IntentEntity,
    IntentException,
    IntentHealth,
    IntentProvider,
    IntentRecognitionError,
    IntentRecognizer,
    IntentResolution,
    IntentResolutionError,
    IntentResolver,
    IntentRuntime,
    IntentRuntimeStatus,
    IntentValidator,
    ResolutionStatistics,
    ResolutionStatus,
    UserIntent,
    get_intent_runtime,
    reset_intent_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global runtime before and after each test."""
    reset_intent_runtime()
    yield
    reset_intent_runtime()


def test_intent_models_defaults_and_immutability() -> None:
    """Verifies Pydantic v2 model default values and immutability."""
    intent = UserIntent(
        category=IntentCategory.FILE_MANAGEMENT,
        raw_prompt="create folder test",
        action="CREATE_FOLDER",
        confidence=IntentConfidence.HIGH,
    )
    assert intent.category == IntentCategory.FILE_MANAGEMENT
    assert intent.confidence == IntentConfidence.HIGH

    with pytest.raises((TypeError, ValidationError)):
        intent.category = IntentCategory.SYSTEM_CONTROL  # type: ignore

    entity = IntentEntity(
        entity_type=EntityType.FOLDER,
        name="target",
        value="Projects",
    )
    assert entity.entity_type == EntityType.FOLDER

    with pytest.raises((TypeError, ValidationError)):
        entity.value = "NewProjects"  # type: ignore


def test_intent_exceptions_hierarchy() -> None:
    """Verifies exception inheritance hierarchy."""
    assert issubclass(IntentRecognitionError, IntentException)
    assert issubclass(IntentResolutionError, IntentException)
    assert issubclass(EntityExtractionError, IntentException)
    assert issubclass(AmbiguousIntentError, IntentException)

    exc = IntentRecognitionError("Failed to parse prompt")
    assert isinstance(exc, IntentException)


def test_intent_recognizer_normalization_and_filler_removal() -> None:
    """Verifies text normalization and conversational filler removal."""
    recognizer = IntentRecognizer()

    raw = "  Hey Auralis, could you please CREATE a folder called Demo!  "
    normalized = recognizer.normalize_text(raw)
    assert "hey auralis" in normalized

    cleaned = recognizer.remove_filler_words(normalized)
    assert "hey auralis" not in cleaned
    assert "could you please" not in cleaned
    assert "create a folder called demo" in cleaned


def test_intent_recognizer_pattern_matching() -> None:
    """Verifies deterministic pattern matching for command categories."""
    recognizer = IntentRecognizer()

    res1 = recognizer.recognize("Please create a folder named Archives")
    assert res1.category == IntentCategory.FILE_MANAGEMENT
    assert res1.action == "CREATE_FOLDER"
    assert res1.confidence == IntentConfidence.HIGH

    res2 = recognizer.recognize("Find all pdf documents in downloads")
    assert res2.category == IntentCategory.FILE_SEARCH
    assert res2.action == "SEARCH_FILE"

    res3 = recognizer.recognize("Launch Chrome browser")
    assert res3.category == IntentCategory.APPLICATION_CONTROL
    assert res3.action == "OPEN_APPLICATION"

    res4 = recognizer.recognize("Mute the system volume")
    assert res4.category == IntentCategory.SYSTEM_CONTROL
    assert res4.action == "MUTE"

    res5 = recognizer.recognize("Turn on wifi")
    assert res5.category == IntentCategory.DEVICE_CONTROL
    assert res5.action == "ENABLE_DEVICE"


def test_intent_recognizer_edge_cases_empty_input() -> None:
    """Verifies recognizer behavior on empty and None inputs."""
    recognizer = IntentRecognizer()

    empty_res = recognizer.recognize("   ")
    assert empty_res.category == IntentCategory.UNKNOWN
    assert empty_res.confidence == IntentConfidence.NONE

    with pytest.raises(IntentRecognitionError):
        recognizer.recognize(None)  # type: ignore


def test_entity_extractor_paths_files_folders() -> None:
    """Verifies extraction of file, folder, and path entities."""
    extractor = EntityExtractor()

    text = "Move file C:\\Users\\Docs\\report.pdf to folder Backup"
    entities = extractor.extract_entities(text)

    types = [e.entity_type for e in entities]
    assert EntityType.PATH in types or EntityType.FILE in types
    assert any(e.value == "Backup" or "report.pdf" in str(e.value) for e in entities)


def test_entity_extractor_apps_numbers_dates_times_devices() -> None:
    """Verifies extraction of applications, numbers, dates, times, and devices."""
    extractor = EntityExtractor()

    text = "Open VS Code and set volume to 50% tomorrow at 5pm on wifi"
    entities = extractor.extract_entities(text)

    types = [e.entity_type for e in entities]
    assert EntityType.APPLICATION in types
    assert EntityType.NUMBER in types
    assert EntityType.DATE in types
    assert EntityType.TIME in types
    assert EntityType.DEVICE_NAME in types

    app_entity = next(e for e in entities if e.entity_type == EntityType.APPLICATION)
    assert app_entity.value == "vs code"

    num_entity = next(e for e in entities if e.entity_type == EntityType.NUMBER)
    assert num_entity.value == 50.0
    assert num_entity.metadata.get("is_percentage") is True


def test_intent_resolver_candidate_scoring_and_context_merging() -> None:
    """Verifies candidate scoring and workspace context merging."""
    recognizer = IntentRecognizer()
    extractor = EntityExtractor()
    resolver = IntentResolver()

    text = "Organize this folder"
    intent = recognizer.recognize(text)
    entities = extractor.extract_entities(text)

    context = IntentContext(
        workspace_context={"active_file": "C:\\Projects\\app.py"}
    )

    resolution = resolver.resolve(text, intent=intent, entities=entities, context=context)
    assert resolution.status == ResolutionStatus.RESOLVED
    assert len(resolution.entities) > 0
    assert resolution.entities[0].value == "C:\\Projects\\app.py"


def test_intent_resolver_ambiguity_handling() -> None:
    """Verifies ambiguity level calculation when multiple targets or low confidence occur."""
    recognizer = IntentRecognizer()
    extractor = EntityExtractor()
    resolver = IntentResolver()

    # Conflicting target files
    text = "Delete file1.txt file2.txt file3.txt"
    intent = recognizer.recognize(text)
    entities = extractor.extract_entities(text)

    resolution = resolver.resolve(text, intent=intent, entities=entities)
    assert resolution.status == ResolutionStatus.AMBIGUOUS
    assert resolution.ambiguity_level == AmbiguityLevel.HIGH


def test_intent_validator_diagnostics_and_dangerous_requests() -> None:
    """Verifies diagnostics reporting for missing parameters and dangerous requests."""
    validator = IntentValidator()

    # Missing application target
    intent1 = UserIntent(category=IntentCategory.APPLICATION_CONTROL, action="OPEN_APPLICATION")
    res1 = IntentResolution(primary_intent=intent1, entities=[])
    diag1 = validator.validate(res1)
    assert any("Missing required application" in d for d in diag1)

    # Dangerous request detection
    intent2 = UserIntent(category=IntentCategory.FILE_MANAGEMENT, raw_prompt="rm -rf /", normalized_text="rm -rf /")
    res2 = IntentResolution(primary_intent=intent2, entities=[])
    diag2 = validator.validate(res2)
    assert any("SECURITY_ALERT" in d for d in diag2)


def test_intent_provider_end_to_end_resolution_and_statistics() -> None:
    """Verifies IntentProvider end-to-end processing and statistics accumulation."""
    provider = IntentProvider()

    res = provider.resolve_intent("Please open Spotify app")
    assert res.status == ResolutionStatus.RESOLVED
    assert res.primary_intent is not None
    assert res.primary_intent.category == IntentCategory.APPLICATION_CONTROL
    assert any(e.value == "spotify" for e in res.entities)

    stats = provider.get_statistics()
    assert isinstance(stats, ResolutionStatistics)
    assert stats.total_resolutions == 1
    assert stats.resolved_count == 1
    assert stats.average_resolution_time_ms >= 0.0

    health = provider.health_check()
    assert isinstance(health, IntentHealth)
    assert health.healthy is True
    assert len(health.components) == 4


def test_intent_runtime_lifecycle_and_singleton_identity() -> None:
    """Verifies IntentRuntime initialization, processing, health checks, and global singleton accessors."""
    rt = get_intent_runtime()
    assert rt.status == IntentRuntimeStatus.READY

    rt2 = get_intent_runtime()
    assert rt is rt2

    res = rt.process_intent("Search for quarterly report.pdf")
    assert res.status == ResolutionStatus.RESOLVED
    assert res.primary_intent.category == IntentCategory.FILE_SEARCH

    health = rt.health_check()
    assert health.healthy is True
    assert health.status == IntentRuntimeStatus.READY

    stats = rt.get_statistics()
    assert stats.total_resolutions == 1

    rt.clear()
    assert rt.get_statistics().total_resolutions == 0

    assert rt.shutdown() is True
    assert rt.status == IntentRuntimeStatus.SHUTDOWN


def test_intent_runtime_thread_safety() -> None:
    """Verifies thread-safe resolution processing across concurrent worker threads."""
    rt = get_intent_runtime()
    prompts = [
        "Create folder Test1",
        "Open Chrome",
        "Mute system volume",
        "Find image vacation.png",
        "Take a screenshot",
    ] * 5

    def worker(p: str) -> ResolutionStatus:
        res = rt.process_intent(p)
        return res.status

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, prompts))

    assert len(results) == 25
    stats = rt.get_statistics()
    assert stats.total_resolutions == 25
    assert stats.resolved_count > 0


def test_conflicting_entities_and_multiple_commands() -> None:
    """Verifies edge case handling for prompts with conflicting entities or multiple targets."""
    provider = IntentProvider()

    # Conflicting target paths for move operation
    text = "Move file.txt from C:\\source\\file.txt to D:\\dest\\file.txt and E:\\other\\file.txt"
    res = provider.resolve_intent(text)
    assert res.status in (ResolutionStatus.AMBIGUOUS, ResolutionStatus.RESOLVED)
    assert len(res.entities) >= 2
