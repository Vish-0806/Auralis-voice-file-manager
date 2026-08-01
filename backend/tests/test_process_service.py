"""Unit tests for ProcessService (Phase 11.4)."""

import os
# pyrefly: ignore [missing-import]
import pytest

from brain.os.process import (
    ProcessNotFoundError,
    ProcessResourceUsage,
    ProcessService,
    RunningProcess,
)


def test_process_service_inspect_current_process() -> None:
    svc = ProcessService()
    curr_pid = os.getpid()

    running = svc.get_running_process(curr_pid)
    assert isinstance(running, RunningProcess)
    assert running.info.process_id == curr_pid
    assert running.memory_bytes > 0

    usage = svc.get_resource_usage(curr_pid)
    assert isinstance(usage, ProcessResourceUsage)
    assert usage.process_id == curr_pid
    assert usage.memory_rss_bytes > 0

    cmdline = svc.get_command_line(curr_pid)
    assert isinstance(cmdline, list)

    cwd = svc.get_working_directory(curr_pid)
    assert isinstance(cwd, str) or cwd is None


def test_process_service_invalid_pid() -> None:
    svc = ProcessService()
    with pytest.raises(ProcessNotFoundError):
        svc.get_running_process(9999999)
