"""Unit tests for the ReferenceResolver service."""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime
from memory.models.domain_models import AssistantContext, MemoryEntry, MemoryMetadata, MemoryType
from brain.planning.reference_resolver import ReferenceResolver


def test_resolver_empty_request() -> None:
    """Verify ReferenceResolver handles empty requests and missing context gracefully."""
    resolver = ReferenceResolver()
    ctx = AssistantContext()

    res = resolver.resolve("", ctx)
    assert res.original_request == ""
    assert res.resolved_request == ""
    assert res.resolved_entities == {}
    assert res.confidence_score == 0.0


def test_resolver_no_matching_entities() -> None:
    """Verify ReferenceResolver preserves original request and returns 0 confidence when no entity matches."""
    resolver = ReferenceResolver()
    ctx = AssistantContext()

    res = resolver.resolve("open it in same folder", ctx)
    assert res.original_request == "open it in same folder"
    assert res.resolved_request == "open it in same folder"
    assert res.resolved_entities == {}
    assert res.confidence_score == 0.0


def test_resolver_same_application_active_window() -> None:
    """Verify 'same application' resolves to the active window in current context."""
    resolver = ReferenceResolver()
    ctx = AssistantContext(
        current_context=MemoryEntry(
            id="sess_1",
            content="/workspace",
            memory_type=MemoryType.SESSION,
            metadata=MemoryMetadata(additional_info={"active_window": "Spotify"})
        )
    )

    res = resolver.resolve("mute same application", ctx)
    assert res.resolved_request == "mute Spotify"
    assert res.resolved_entities == {"application": "Spotify"}
    assert res.confidence_score == 1.0


def test_resolver_same_application_recent_executions() -> None:
    """Verify 'same app' resolves to target application in recent executions if active window is missing."""
    resolver = ReferenceResolver()
    ctx = AssistantContext(
        recent_executions=[
            MemoryEntry(
                id="exec_1",
                content="Execution completed",
                memory_type=MemoryType.ACTIVITY,
                metadata=MemoryMetadata(
                    additional_info={
                        "action": "OPEN_APPLICATION",
                        "input_parameters": {"target": "Google Chrome"}
                    }
                )
            )
        ]
    )

    res = resolver.resolve("close same app", ctx)
    assert res.resolved_request == "close Google Chrome"
    assert res.resolved_entities == {"application": "Google Chrome"}
    assert res.confidence_score == 1.0


def test_resolver_same_folder() -> None:
    """Verify 'same folder' and 'same directory' resolve to active workspace path."""
    resolver = ReferenceResolver()
    ctx = AssistantContext(
        current_context=MemoryEntry(
            id="sess_1",
            content="C:\\Users\\User\\Project",
            memory_type=MemoryType.SESSION,
        )
    )

    res = resolver.resolve("list same folder", ctx)
    assert res.resolved_request == "list C:\\Users\\User\\Project"
    assert res.resolved_entities == {"folder": "C:\\Users\\User\\Project"}
    assert res.confidence_score == 1.0

    res2 = resolver.resolve("clean same directory", ctx)
    assert res2.resolved_request == "clean C:\\Users\\User\\Project"


def test_resolver_same_file() -> None:
    """Verify 'same file' resolves to the last file processed from executions or conversations."""
    resolver = ReferenceResolver()
    ctx = AssistantContext(
        recent_executions=[
            MemoryEntry(
                id="exec_1",
                content="Copied",
                memory_type=MemoryType.ACTIVITY,
                metadata=MemoryMetadata(
                    additional_info={
                        "input_parameters": {"file_path": "notes.txt"}
                    }
                )
            )
        ]
    )

    res = resolver.resolve("delete same file", ctx)
    assert res.resolved_request == "delete notes.txt"
    assert res.resolved_entities == {"file": "notes.txt"}
    assert res.confidence_score == 1.0


def test_resolver_previous_and_pronouns() -> None:
    """Verify 'previous', 'last one', and pronouns ('it') resolve to the latest execution target."""
    resolver = ReferenceResolver()
    ctx = AssistantContext(
        recent_executions=[
            MemoryEntry(
                id="exec_1",
                content="Completed",
                memory_type=MemoryType.ACTIVITY,
                metadata=MemoryMetadata(
                    additional_info={
                        "input_parameters": {"target": "Chrome"}
                    }
                )
            )
        ]
    )

    res1 = resolver.resolve("open previous", ctx)
    assert res1.resolved_request == "open Chrome"
    assert res1.resolved_entities == {"previous": "Chrome"}
    assert res1.confidence_score == 1.0

    res2 = resolver.resolve("close it", ctx)
    assert res2.resolved_request == "close Chrome"
    assert res2.resolved_entities == {"pronoun": "Chrome"}
    assert res2.confidence_score == 1.0
