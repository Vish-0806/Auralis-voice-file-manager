"""Unit tests for voice_models.py (Phase 9.6)."""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.voice import (
    VoiceCommand, VoiceCommandStatus, VoiceInteractionType,
    VoiceResponse, VoiceConfirmation, ConfirmationStatus,
    VoiceClarification, ClarificationStatus,
    VoiceFeedback, VoiceSessionState,
    VoiceInteractionResult, VoiceRuntimeHealth, VoiceRuntimeStatistics,
)


# ---------------------------------------------------------------------------
# VoiceCommand
# ---------------------------------------------------------------------------

def test_voice_command_defaults() -> None:
    cmd = VoiceCommand()
    assert cmd.command_id == ""
    assert cmd.status == VoiceCommandStatus.RECEIVED
    assert cmd.confidence == 1.0
    assert cmd.language == "en"
    assert cmd.requires_confirmation is False
    assert cmd.requires_clarification is False


def test_voice_command_frozen() -> None:
    cmd = VoiceCommand(command_id="c1", raw_text="delete downloads")
    with pytest.raises((TypeError, ValidationError)):
        cmd.raw_text = "other"


def test_voice_command_metadata_dict() -> None:
    cmd = VoiceCommand(metadata={"key": "value"})
    assert cmd.metadata["key"] == "value"


def test_voice_command_all_statuses() -> None:
    for s in VoiceCommandStatus:
        cmd = VoiceCommand(status=s)
        assert cmd.status == s


def test_voice_command_received_at_set() -> None:
    cmd = VoiceCommand()
    assert isinstance(cmd.received_at, datetime)


# ---------------------------------------------------------------------------
# VoiceResponse
# ---------------------------------------------------------------------------

def test_voice_response_defaults() -> None:
    r = VoiceResponse()
    assert r.success is True
    assert r.interaction_type == VoiceInteractionType.FEEDBACK


def test_voice_response_frozen() -> None:
    r = VoiceResponse(text="hello")
    with pytest.raises((TypeError, ValidationError)):
        r.text = "changed"


def test_voice_response_all_interaction_types() -> None:
    for t in VoiceInteractionType:
        r = VoiceResponse(interaction_type=t)
        assert r.interaction_type == t


# ---------------------------------------------------------------------------
# VoiceConfirmation
# ---------------------------------------------------------------------------

def test_voice_confirmation_defaults() -> None:
    c = VoiceConfirmation()
    assert c.status == ConfirmationStatus.PENDING
    assert c.response is None
    assert c.timeout_seconds == 30.0


def test_voice_confirmation_frozen() -> None:
    c = VoiceConfirmation(prompt="Are you sure?")
    with pytest.raises((TypeError, ValidationError)):
        c.prompt = "Changed"


def test_voice_confirmation_all_statuses() -> None:
    for s in ConfirmationStatus:
        c = VoiceConfirmation(status=s)
        assert c.status == s


# ---------------------------------------------------------------------------
# VoiceClarification
# ---------------------------------------------------------------------------

def test_voice_clarification_defaults() -> None:
    c = VoiceClarification()
    assert c.status == ClarificationStatus.PENDING
    assert c.options == []
    assert c.selected_option is None


def test_voice_clarification_frozen() -> None:
    c = VoiceClarification(prompt="Which one?", options=["a", "b"])
    with pytest.raises((TypeError, ValidationError)):
        c.prompt = "Changed"


def test_voice_clarification_with_options() -> None:
    c = VoiceClarification(options=["report.pdf", "report.docx"])
    assert len(c.options) == 2


def test_voice_clarification_all_statuses() -> None:
    for s in ClarificationStatus:
        c = VoiceClarification(status=s)
        assert c.status == s


# ---------------------------------------------------------------------------
# VoiceFeedback
# ---------------------------------------------------------------------------

def test_voice_feedback_defaults() -> None:
    f = VoiceFeedback()
    assert f.success is True
    assert f.duration_ms == 0.0
    assert f.text == ""


def test_voice_feedback_frozen() -> None:
    f = VoiceFeedback(text="Done.")
    with pytest.raises((TypeError, ValidationError)):
        f.text = "Changed"


# ---------------------------------------------------------------------------
# VoiceSessionState
# ---------------------------------------------------------------------------

def test_voice_session_state_all_values() -> None:
    states = {s.value for s in VoiceSessionState}
    assert "IDLE" in states
    assert "ACTIVE" in states
    assert "CONFIRMING" in states
    assert "CLARIFYING" in states
    assert "PROCESSING" in states
    assert "ENDED" in states


# ---------------------------------------------------------------------------
# VoiceInteractionResult
# ---------------------------------------------------------------------------

def test_voice_interaction_result_defaults() -> None:
    r = VoiceInteractionResult()
    assert r.success is True
    assert r.status == VoiceCommandStatus.COMPLETED
    assert r.pipeline_ms == 0.0
    assert r.confirmation_required is False
    assert r.clarification_required is False


def test_voice_interaction_result_frozen() -> None:
    r = VoiceInteractionResult()
    with pytest.raises((TypeError, ValidationError)):
        r.success = False


def test_voice_interaction_result_with_feedback() -> None:
    fb = VoiceFeedback(text="Done.")
    r = VoiceInteractionResult(feedback=fb)
    assert r.feedback.text == "Done."


# ---------------------------------------------------------------------------
# VoiceRuntimeHealth
# ---------------------------------------------------------------------------

def test_voice_runtime_health_defaults() -> None:
    h = VoiceRuntimeHealth()
    assert h.healthy is True
    assert h.active_sessions == 0
    assert isinstance(h.registered_components, list)


def test_voice_runtime_health_frozen() -> None:
    h = VoiceRuntimeHealth()
    with pytest.raises((TypeError, ValidationError)):
        h.healthy = False


# ---------------------------------------------------------------------------
# VoiceRuntimeStatistics
# ---------------------------------------------------------------------------

def test_voice_runtime_statistics_defaults() -> None:
    s = VoiceRuntimeStatistics()
    assert s.commands_received == 0
    assert s.sessions_started == 0
    assert s.average_pipeline_ms == 0.0


def test_voice_runtime_statistics_frozen() -> None:
    s = VoiceRuntimeStatistics()
    with pytest.raises((TypeError, ValidationError)):
        s.commands_received = 99
