"""Unit tests for brain_models.py (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.runtime import (
    BrainRequest, BrainResponse, BrainRuntimeHealth, BrainRuntimeStatistics,
    PipelineResult, PipelineStatus, RuntimeComponent, SubsystemHealth, SubsystemStatistics,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

def test_runtime_component_values() -> None:
    values = {c.value for c in RuntimeComponent}
    assert "VOICE" in values
    assert "CONVERSATION" in values
    assert "REASONING" in values
    assert "PLANNING" in values
    assert "EXECUTION" in values
    assert "FILESYSTEM" in values
    assert "BRAIN" in values


def test_pipeline_status_values() -> None:
    values = {s.value for s in PipelineStatus}
    assert "INITIALIZING" in values
    assert "PENDING" in values
    assert "COMPLETED" in values
    assert "FAILED" in values
    assert "CANCELLED" in values


# ---------------------------------------------------------------------------
# BrainRequest & BrainResponse
# ---------------------------------------------------------------------------

def test_brain_request_defaults() -> None:
    req = BrainRequest(raw_text="hello")
    assert req.raw_text == "hello"
    assert req.request_id == ""
    assert req.session_id == ""
    assert req.confidence == 1.0
    assert isinstance(req.timestamp, datetime)


def test_brain_request_frozen() -> None:
    req = BrainRequest(raw_text="hello")
    with pytest.raises((TypeError, ValidationError)):
        req.raw_text = "changed"


def test_brain_response_defaults() -> None:
    res = BrainResponse()
    assert res.success is True
    assert res.pipeline_status == PipelineStatus.COMPLETED
    assert res.duration_ms == 0.0


def test_brain_response_frozen() -> None:
    res = BrainResponse(text="hi")
    with pytest.raises((TypeError, ValidationError)):
        res.text = "changed"


# ---------------------------------------------------------------------------
# SubsystemHealth & SubsystemStatistics
# ---------------------------------------------------------------------------

def test_subsystem_health_defaults() -> None:
    sh = SubsystemHealth(subsystem_name="VOICE")
    assert sh.subsystem_name == "VOICE"
    assert sh.healthy is True
    assert sh.status == "READY"


def test_subsystem_health_frozen() -> None:
    sh = SubsystemHealth(subsystem_name="VOICE")
    with pytest.raises((TypeError, ValidationError)):
        sh.healthy = False


def test_subsystem_statistics_defaults() -> None:
    ss = SubsystemStatistics(subsystem_name="VOICE", stats={"count": 5})
    assert ss.subsystem_name == "VOICE"
    assert ss.stats["count"] == 5


# ---------------------------------------------------------------------------
# BrainRuntimeHealth & BrainRuntimeStatistics
# ---------------------------------------------------------------------------

def test_brain_runtime_health_defaults() -> None:
    h = BrainRuntimeHealth()
    assert h.healthy is True
    assert h.status == "READY"
    assert h.active_requests == 0


def test_brain_runtime_health_frozen() -> None:
    h = BrainRuntimeHealth()
    with pytest.raises((TypeError, ValidationError)):
        h.healthy = False


def test_brain_runtime_statistics_defaults() -> None:
    st = BrainRuntimeStatistics()
    assert st.total_requests == 0
    assert st.successful_requests == 0
    assert st.average_pipeline_ms == 0.0


def test_brain_runtime_statistics_frozen() -> None:
    st = BrainRuntimeStatistics()
    with pytest.raises((TypeError, ValidationError)):
        st.total_requests = 10


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------

def test_pipeline_result_defaults() -> None:
    pr = PipelineResult()
    assert pr.success is True
    assert pr.status == PipelineStatus.COMPLETED
    assert pr.pipeline_ms == 0.0


def test_pipeline_result_frozen() -> None:
    pr = PipelineResult()
    with pytest.raises((TypeError, ValidationError)):
        pr.success = False
