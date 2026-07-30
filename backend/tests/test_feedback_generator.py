"""Unit tests for FeedbackGenerator (Phase 9.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.voice import (
    FeedbackGenerator, VoiceCommand, VoiceFeedback,
    VoiceInteractionResult, VoiceCommandStatus,
)


@pytest.fixture
def generator() -> FeedbackGenerator:
    return FeedbackGenerator()


# ---------------------------------------------------------------------------
# Generate from Result
# ---------------------------------------------------------------------------

def test_generate_success_copy(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="copy report.pdf to downloads")
    res = VoiceInteractionResult(command_id="c1", success=True)
    fb = generator.generate(cmd, res)
    assert isinstance(fb, VoiceFeedback)
    assert fb.success is True
    assert "Copy completed" in fb.text


def test_generate_success_delete(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="delete temp.txt")
    res = VoiceInteractionResult(command_id="c1", success=True)
    fb = generator.generate(cmd, res)
    assert "Deletion completed" in fb.text


def test_generate_success_search(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="search downloads")
    res = VoiceInteractionResult(command_id="c1", success=True)
    fb = generator.generate(cmd, res)
    assert "Search completed" in fb.text


def test_generate_success_generic(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="do something custom")
    res = VoiceInteractionResult(command_id="c1", success=True)
    fb = generator.generate(cmd, res)
    assert "Execution completed successfully" in fb.text


def test_generate_failure_permission(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="delete system.dll")
    res = VoiceInteractionResult(command_id="c1", success=False, error="permission denied")
    fb = generator.generate(cmd, res)
    assert fb.success is False
    assert "Permission denied" in fb.text


def test_generate_failure_not_found(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="open missing.txt")
    res = VoiceInteractionResult(command_id="c1", success=False, error="File not found")
    fb = generator.generate(cmd, res)
    assert "not found" in fb.text


def test_generate_failure_generic(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="test")
    res = VoiceInteractionResult(command_id="c1", success=False, error="unknown error")
    fb = generator.generate(cmd, res)
    assert "Something went wrong" in fb.text


# ---------------------------------------------------------------------------
# Specific Feedback Generators
# ---------------------------------------------------------------------------

def test_generate_started(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(raw_text="list files")
    fb = generator.generate_started(cmd)
    assert "Processing: list files." in fb.text


def test_generate_cancelled(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand(raw_text="copy all")
    fb = generator.generate_cancelled(cmd)
    assert fb.success is False
    assert "Operation cancelled." in fb.text


def test_generate_confirmation_request(generator: FeedbackGenerator) -> None:
    fb = generator.generate_confirmation_request("Are you sure?")
    assert fb.text == "Are you sure?"


def test_generate_clarification_request(generator: FeedbackGenerator) -> None:
    fb = generator.generate_clarification_request("Which one?", options=["doc1.txt", "doc2.txt"])
    assert "Which one? Options: doc1.txt, doc2.txt." in fb.text


def test_generate_permission_denied(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand()
    fb = generator.generate_permission_denied(cmd)
    assert fb.success is False
    assert "Permission denied" in fb.text


def test_generate_confirmation_accepted(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand()
    fb = generator.generate_confirmation_accepted(cmd)
    assert fb.success is True
    assert "Confirmed. Proceeding." in fb.text


def test_generate_confirmation_rejected(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand()
    fb = generator.generate_confirmation_rejected(cmd)
    assert fb.success is False
    assert "Operation cancelled." in fb.text


def test_generate_timeout(generator: FeedbackGenerator) -> None:
    cmd = VoiceCommand()
    fb = generator.generate_timeout(cmd)
    assert fb.success is False
    assert "timeout" in fb.text.lower()
