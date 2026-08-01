"""Unit tests for Phase 11.4 Process Runtime domain models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os.process import (
    ProcessCapabilities,
    ProcessHealth,
    ProcessInfo,
    ProcessLaunchInfo,
    ProcessResourceUsage,
    ProcessRuntimeStatus,
    ProcessState,
    ProcessStatistics,
    ProcessTerminationResult,
    RunningProcess,
    TerminationMode,
    TimeoutPolicy,
)


def test_process_enums() -> None:
    assert ProcessState.RUNNING.value == "running"
    assert ProcessState.SLEEPING.value == "sleeping"
    assert ProcessState.STOPPED.value == "stopped"

    assert TerminationMode.GRACEFUL.value == "graceful"
    assert TerminationMode.FORCE.value == "force"

    assert TimeoutPolicy.WAIT.value == "wait"
    assert TimeoutPolicy.NOWAIT.value == "nowait"


def test_process_info_defaults_and_immutability() -> None:
    info = ProcessInfo(process_id=1234, name="python.exe")
    assert info.process_id == 1234
    assert info.name == "python.exe"
    assert info.state == ProcessState.UNKNOWN

    with pytest.raises((TypeError, ValidationError)):
        info.name = "other"  # type: ignore


def test_running_process_defaults_and_immutability() -> None:
    info = ProcessInfo(process_id=5678, name="notepad")
    proc = RunningProcess(info=info, cpu_percent=1.5, memory_bytes=1048576)
    assert proc.info.process_id == 5678
    assert proc.cpu_percent == 1.5
    assert proc.memory_bytes == 1048576

    with pytest.raises((TypeError, ValidationError)):
        proc.cpu_percent = 2.0  # type: ignore


def test_process_resource_usage_defaults_and_immutability() -> None:
    usage = ProcessResourceUsage(process_id=100, cpu_percent=10.0, memory_rss_bytes=2048)
    assert usage.process_id == 100
    assert usage.cpu_percent == 10.0

    with pytest.raises((TypeError, ValidationError)):
        usage.cpu_percent = 0.0  # type: ignore


def test_process_termination_result_defaults_and_immutability() -> None:
    res = ProcessTerminationResult(success=True, process_id=99, mode=TerminationMode.GRACEFUL)
    assert res.success is True
    assert res.process_id == 99

    with pytest.raises((TypeError, ValidationError)):
        res.success = False  # type: ignore
