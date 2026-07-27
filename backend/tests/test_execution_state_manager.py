"""Unit tests for the ExecutionStateManager service."""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
import pytest

from brain.execution.execution_state import ExecutionStatus, ExecutionSnapshot
from brain.execution.execution_state_manager import ExecutionStateManager


def test_manager_create_execution() -> None:
    """Verifies that create_execution initializes a new state and snapshot history."""
    mgr = ExecutionStateManager()
    state = mgr.create_execution(execution_id="exec_1", user_id=42, workflow_id="wf_abc")
    
    assert state.execution_id == "exec_1"
    assert state.user_id == 42
    assert state.workflow_id == "wf_abc"
    assert state.status == ExecutionStatus.QUEUED

    history = mgr.get_snapshot_history("exec_1")
    assert len(history) == 1
    assert history[0].status == ExecutionStatus.QUEUED


def test_manager_get_execution() -> None:
    """Verifies get_execution retrieves correct state and returns None for unknown IDs."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    state = mgr.get_execution("exec_1")
    assert state is not None
    assert state.execution_id == "exec_1"

    assert mgr.get_execution("unknown_id") is None


def test_manager_list_active_and_finished() -> None:
    """Verifies list_active and list_finished partition executions correctly."""
    mgr = ExecutionStateManager()
    
    # 1. QUEUED (Active)
    mgr.create_execution(execution_id="exec_1", user_id=42)

    # 2. RUNNING (Active)
    state2 = mgr.create_execution(execution_id="exec_2", user_id=42)
    mgr.mark_running("exec_2")

    # 3. COMPLETED (Finished)
    state3 = mgr.create_execution(execution_id="exec_3", user_id=42)
    mgr.mark_completed("exec_3")

    active = mgr.list_active()
    assert len(active) == 2
    assert {s.execution_id for s in active} == {"exec_1", "exec_2"}

    finished = mgr.list_finished()
    assert len(finished) == 1
    assert finished[0].execution_id == "exec_3"


def test_manager_update_progress() -> None:
    """Verifies update_progress updates details and appends new snapshot."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    success = mgr.update_progress(
        execution_id="exec_1",
        percentage=20.0,
        current_step=1,
        total_steps=5,
        current_operation="Step 1",
    )
    assert success is True

    state = mgr.get_execution("exec_1")
    assert state.progress.percentage == 20.0
    assert state.progress.current_operation == "Step 1"

    history = mgr.get_snapshot_history("exec_1")
    assert len(history) == 2  # initial + progress update
    assert history[1].percentage == 20.0


def test_manager_status_transitions() -> None:
    """Verifies mark_running and mark_paused transition states properly."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    assert mgr.mark_running("exec_1") is True
    assert mgr.get_execution("exec_1").status == ExecutionStatus.RUNNING

    assert mgr.mark_paused("exec_1") is True
    assert mgr.get_execution("exec_1").status == ExecutionStatus.PAUSED


def test_manager_retry_count() -> None:
    """Verifies that mark_retrying increments the retry count."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    assert mgr.mark_retrying("exec_1") is True
    state = mgr.get_execution("exec_1")
    assert state.status == ExecutionStatus.RETRYING
    assert state.retry_count == 1


def test_manager_completed_state() -> None:
    """Verifies mark_completed transitions state and progress metrics."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    assert mgr.mark_completed("exec_1") is True
    state = mgr.get_execution("exec_1")
    assert state.status == ExecutionStatus.COMPLETED
    assert state.progress.percentage == 100.0


def test_manager_failed_state() -> None:
    """Verifies mark_failed sets error details and terminal timestamps."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    assert mgr.mark_failed("exec_1", "Out of disk space") is True
    state = mgr.get_execution("exec_1")
    assert state.status == ExecutionStatus.FAILED
    assert state.error_message == "Out of disk space"


def test_manager_cancelled_state() -> None:
    """Verifies mark_cancelled updates state and terminates progress."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    assert mgr.mark_cancelled("exec_1") is True
    state = mgr.get_execution("exec_1")
    assert state.status == ExecutionStatus.CANCELLED
    assert state.progress.completed_at is not None


def test_manager_snapshot_history() -> None:
    """Verifies snapshot list retrieval is chronological."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)
    
    mgr.update_progress("exec_1", percentage=25.0, current_step=1, total_steps=4)
    mgr.update_progress("exec_1", percentage=50.0, current_step=2, total_steps=4)
    mgr.update_progress("exec_1", percentage=75.0, current_step=3, total_steps=4)
    
    history = mgr.get_snapshot_history("exec_1")
    assert len(history) == 4
    assert history[0].percentage == 0.0
    assert history[1].percentage == 25.0
    assert history[2].percentage == 50.0
    assert history[3].percentage == 75.0


def test_manager_remove_execution() -> None:
    """Verifies that remove_execution deletes the state and snapshot references."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)

    assert mgr.remove_execution("exec_1") is True
    assert mgr.get_execution("exec_1") is None
    assert mgr.get_snapshot_history("exec_1") == []


def test_manager_clear() -> None:
    """Verifies that clear deletes all state logs in-memory."""
    mgr = ExecutionStateManager()
    mgr.create_execution(execution_id="exec_1", user_id=42)
    mgr.create_execution(execution_id="exec_2", user_id=42)

    mgr.clear()
    assert len(mgr.list_active()) == 0
    assert mgr.get_execution("exec_1") is None


def test_manager_unknown_execution_ids() -> None:
    """Verifies that calling methods with unknown IDs returns False gracefully."""
    mgr = ExecutionStateManager()
    
    assert mgr.get_execution("nonexistent") is None
    assert mgr.update_progress("nonexistent", 50.0, 1, 2) is False
    assert mgr.mark_running("nonexistent") is False
    assert mgr.mark_paused("nonexistent") is False
    assert mgr.mark_retrying("nonexistent") is False
    assert mgr.mark_completed("nonexistent") is False
    assert mgr.mark_failed("nonexistent", "error") is False
    assert mgr.mark_cancelled("nonexistent") is False
    assert mgr.remove_execution("nonexistent") is False
    assert mgr.get_snapshot_history("nonexistent") == []


def test_manager_thread_safety() -> None:
    """Simulates basic concurrent access to verify thread safety (RLock)."""
    mgr = ExecutionStateManager()

    def run_worker(thread_num: int):
        exec_id = f"thread_exec_{thread_num}"
        # Create execution
        mgr.create_execution(execution_id=exec_id, user_id=thread_num)
        # Update progress multiple times
        for step in range(1, 4):
            mgr.update_progress(
                execution_id=exec_id,
                percentage=step * 33.3,
                current_step=step,
                total_steps=3,
            )
        # Complete
        mgr.mark_completed(exec_id)

    # Spawn 10 concurrent threads running workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_worker, i) for i in range(10)]
        concurrent.futures.wait(futures)

    # All executions should be created and marked COMPLETED
    finished = mgr.list_finished()
    assert len(finished) == 10
    for state in finished:
        assert state.status == ExecutionStatus.COMPLETED
        assert state.progress.percentage == 100.0
        assert len(mgr.get_snapshot_history(state.execution_id)) == 5  # init + 3 progress + completed
