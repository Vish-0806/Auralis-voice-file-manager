"""Unit tests for ProcessController (Phase 11.4)."""

import os
import subprocess
import sys
# pyrefly: ignore [missing-import]
import pytest

from brain.os.process import (
    ProcessController,
    ProcessPermissionError,
    ProcessTerminationResult,
    TerminationMode,
)


def test_process_controller_terminate_subprocess() -> None:
    # Spawn a temporary child subprocess
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
    pid = proc.pid

    ctrl = ProcessController()

    res = ctrl.terminate_process(pid, mode=TerminationMode.GRACEFUL, timeout_seconds=5.0)
    assert isinstance(res, ProcessTerminationResult)
    assert res.success is True
    assert res.process_id == pid


def test_process_controller_safety_validation() -> None:
    ctrl = ProcessController()
    curr_pid = os.getpid()

    # Self-termination protection
    with pytest.raises(ProcessPermissionError):
        ctrl.terminate_process(curr_pid)

    # Critical PID protection
    with pytest.raises(ProcessPermissionError):
        ctrl.terminate_process(0)
