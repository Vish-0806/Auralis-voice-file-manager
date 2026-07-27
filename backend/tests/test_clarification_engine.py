"""Unit tests for the Interactive Clarification Engine."""

from __future__ import annotations

import time
# pyrefly: ignore [missing-import]
import pytest
from typing import Any

from core.models import ExecutionPlan as CoreExecutionPlan
from core.intents import Intent
from brain.execution.clarification_engine import (
    ClarificationEngine,
    ClarificationContext,
    ClarificationType,
    ClarificationRequest,
    ClarificationResponse,
    ClarificationChoice,
)


class MockExecutionStep:
    """Mock execution step to simulate target and parameters."""
    def __init__(self, intent: Intent, target: str | None = None, parameters: dict | None = None) -> None:
        self.intent = intent
        self.target = target
        self.parameters = parameters or {}


def test_clarification_missing_target() -> None:
    """Verifies that MISSING_TARGET is detected when target is empty."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.OPEN_APPLICATION, target=None)
    context = ClarificationContext(execution_step=step)

    assert engine.detect_clarification(context) is True
    req = engine.generate_request(context)
    assert req is not None
    assert req.type == ClarificationType.MISSING_TARGET
    assert req.required is True


def test_clarification_multiple_matches_workspace() -> None:
    """Verifies that WORKSPACE_SELECTION is detected when multiple projects exist."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.DELETE_FOLDER, target="project")
    context = ClarificationContext(
        execution_step=step,
        workspace_analysis={"projects": ["Project Alpha", "Project Beta"], "multiple_projects": True}
    )

    assert engine.detect_clarification(context) is True
    req = engine.generate_request(context)
    assert req is not None
    assert req.type == ClarificationType.WORKSPACE_SELECTION
    assert len(req.choices) == 2
    assert req.choices[0].label == "Project Alpha"


def test_clarification_application_selection() -> None:
    """Verifies that APPLICATION_SELECTION is detected for multiple installed browsers."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.OPEN_APPLICATION, target="browser")
    context = ClarificationContext(
        execution_step=step,
        resolved_preferences={"browsers": ["Chrome", "Firefox", "Edge"]}
    )

    assert engine.detect_clarification(context) is True
    req = engine.generate_request(context)
    assert req is not None
    assert req.type == ClarificationType.APPLICATION_SELECTION
    assert len(req.choices) == 3


def test_clarification_file_selection() -> None:
    """Verifies that FILE_SELECTION is detected when wildcard maps to multiple files."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.DRAG_DROP, target="file")
    context = ClarificationContext(
        execution_step=step,
        workspace_analysis={"matched_files": ["log.txt", "notes.txt"]}
    )

    assert engine.detect_clarification(context) is True
    req = engine.generate_request(context)
    assert req is not None
    assert req.type == ClarificationType.FILE_SELECTION
    assert len(req.choices) == 2


def test_clarification_confirmation_required() -> None:
    """Verifies that CONFIRMATION type is generated for high-risk operations via metadata flags."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.DELETE_FOLDER, target="Downloads")
    context = ClarificationContext(execution_step=step, metadata={"needs_confirmation": True})

    assert engine.detect_clarification(context) is True
    req = engine.generate_request(context)
    assert req is not None
    assert req.type == ClarificationType.CONFIRMATION


def test_clarification_missing_parameter() -> None:
    """Verifies that MISSING_PARAMETER is detected when destination folder is empty."""
    engine = ClarificationEngine()
    # Move action missing destination path
    step = MockExecutionStep(intent=Intent.DRAG_DROP, target="file.txt", parameters={"destination": None})
    context = ClarificationContext(execution_step=step)

    assert engine.detect_clarification(context) is True
    req = engine.generate_request(context)
    assert req is not None
    assert req.type == ClarificationType.MISSING_PARAMETER


def test_clarification_ambiguous_intent() -> None:
    """Verifies that general ambiguous intents map to AMBIGUOUS_INTENT."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.UNKNOWN, target="something")
    context = ClarificationContext(execution_step=step)

    assert engine.detect_clarification(context) is True
    req = engine.generate_request(context)
    assert req is not None
    assert req.type == ClarificationType.AMBIGUOUS_INTENT


def test_clarification_no_clarification_needed() -> None:
    """Verifies that detect_clarification returns False if target/parameters are clear."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.OPEN_APPLICATION, target="Chrome", parameters={"confirm_required": False})
    context = ClarificationContext(
        execution_step=step,
        workspace_analysis={"projects": ["Project Alpha"]},
        resolved_preferences={"browsers": ["Chrome"]}
    )

    assert engine.detect_clarification(context) is False
    assert engine.generate_request(context) is None


def test_clarification_response_validation_success() -> None:
    """Verifies response validation succeeds when selected choice matches request choices."""
    engine = ClarificationEngine()
    req = ClarificationRequest(
        clarification_id="clar_test_1",
        type=ClarificationType.APPLICATION_SELECTION,
        question="Select browser?",
        choices=[
            ClarificationChoice(id="chrome", label="Chrome"),
            ClarificationChoice(id="firefox", label="Firefox")
        ],
    )
    resp = ClarificationResponse(
        clarification_id="clar_test_1",
        selected_choice="chrome",
        confirmed=True,
        timestamp=time.time()
    )

    assert engine.validate_response(req, resp) is True


def test_clarification_response_validation_wrong_id() -> None:
    """Verifies response validation fails when IDs do not match."""
    engine = ClarificationEngine()
    req = ClarificationRequest(
        clarification_id="clar_test_req",
        type=ClarificationType.APPLICATION_SELECTION,
        question="Select browser?",
        choices=[ClarificationChoice(id="chrome", label="Chrome")],
    )
    resp = ClarificationResponse(
        clarification_id="clar_test_wrong",
        selected_choice="chrome",
        confirmed=True,
        timestamp=time.time()
    )

    assert engine.validate_response(req, resp) is False


def test_clarification_response_validation_invalid_choice() -> None:
    """Verifies response validation fails when choice is not present in options."""
    engine = ClarificationEngine()
    req = ClarificationRequest(
        clarification_id="clar_test_1",
        type=ClarificationType.APPLICATION_SELECTION,
        question="Select browser?",
        choices=[ClarificationChoice(id="chrome", label="Chrome")],
    )
    resp = ClarificationResponse(
        clarification_id="clar_test_1",
        selected_choice="safari",  # Invalid choice
        confirmed=True,
        timestamp=time.time()
    )

    assert engine.validate_response(req, resp) is False


def test_clarification_apply_response() -> None:
    """Verifies that applying response merges metadata back into context."""
    engine = ClarificationEngine()
    context = ClarificationContext(metadata={"clarification_id": "clar_apply"})
    resp = ClarificationResponse(
        clarification_id="clar_apply",
        selected_choice="firefox",
        confirmed=True,
        timestamp=12345.6
    )

    engine.apply_response(context, resp)
    assert context.metadata["resolved_choice"] == "firefox"
    assert context.metadata["confirmed"] is True
    assert context.metadata["resolved_timestamp"] == 12345.6


def test_clarification_timeout_defaults() -> None:
    """Verifies timeout default values are preserved or parsed correctly."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.DELETE_FOLDER, target="Downloads")
    # Timeout override in metadata
    context = ClarificationContext(execution_step=step, metadata={"timeout_seconds": 120, "needs_confirmation": True})

    req = engine.generate_request(context)
    assert req is not None
    assert req.timeout_seconds == 120

    # Default timeout check
    context_default = ClarificationContext(execution_step=step, metadata={"needs_confirmation": True})
    req_default = engine.generate_request(context_default)
    assert req_default is not None
    assert req_default.timeout_seconds == 60


def test_clarification_metadata_preservation() -> None:
    """Verifies that context metadata tags are preserved during request creation."""
    engine = ClarificationEngine()
    step = MockExecutionStep(intent=Intent.DELETE_FOLDER, target="Downloads")
    context = ClarificationContext(execution_step=step, metadata={"custom_key": "custom_val"})

    # Check context metadata exists
    assert context.metadata.get("custom_key") == "custom_val"
