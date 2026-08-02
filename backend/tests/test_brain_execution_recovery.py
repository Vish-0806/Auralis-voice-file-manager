"""Unit test suite for Phase 12.8 — Execution Recovery & State Management Runtime.

Covers:
- Recovery models, enums, defaults, and immutability
- Subsystem exception hierarchy
- CheckpointManager creation, sorting, querying, and validation error handling
- StateStore snapshot saving, context loading, and validation
- RecoveryEngine plan generation and execution across strategies
- RollbackManager plan creation and step reversal execution
- RecoveryProvider end-to-end processing, health reporting, and statistics
- RecoveryRuntime singleton lifecycle, status management, and thread safety under concurrency
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.recovery import (
    CheckpointError,
    CheckpointManager,
    CheckpointType,
    ExecutionCheckpoint,
    ExecutionState,
    IRecoveryProvider,
    RecoveryEngine,
    RecoveryException,
    RecoveryExecution,
    RecoveryHealth,
    RecoveryPlan,
    RecoveryProvider,
    RecoveryRuntime,
    RecoveryRuntimeStatus,
    RecoveryStatistics,
    RecoveryStatus,
    RecoveryStrategy,
    RollbackExecution,
    RollbackManager,
    RollbackPlan,
    RollbackStatus,
    SnapshotType,
    StateSnapshot,
    StateStore,
    StateStoreError,
    get_recovery_runtime,
    reset_recovery_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global recovery runtime before and after each test."""
    reset_recovery_runtime()
    yield
    reset_recovery_runtime()


def test_recovery_models_defaults_and_immutability() -> None:
    """Verifies recovery model default properties and Pydantic v2 immutability."""
    chk = ExecutionCheckpoint(
        execution_id="exec_1",
        checkpoint_type=CheckpointType.STAGE,
        step_index=2,
        state_data={"completed_step": "step_2"},
    )
    assert chk.execution_id == "exec_1"
    assert chk.checkpoint_type == CheckpointType.STAGE
    assert chk.step_index == 2

    with pytest.raises((TypeError, ValidationError)):
        chk.step_index = 5  # type: ignore

    snap = StateSnapshot(execution_id="exec_1", context_data={"key": "val"})
    assert snap.execution_id == "exec_1"

    with pytest.raises((TypeError, ValidationError)):
        snap.execution_id = "exec_2"  # type: ignore


def test_recovery_exceptions_hierarchy() -> None:
    """Verifies exception inheritance hierarchy."""
    exc = CheckpointError("Checkpoint creation failed")
    assert isinstance(exc, RecoveryException)


def test_checkpoint_manager_creation_and_query() -> None:
    """Verifies CheckpointManager creation, sorting, and latest checkpoint retrieval."""
    mgr = CheckpointManager()

    chk1 = mgr.create_checkpoint("exec_100", CheckpointType.STEP, {"step": 1}, step_index=1)
    chk2 = mgr.create_checkpoint("exec_100", CheckpointType.STEP, {"step": 2}, step_index=2)

    assert mgr.count_checkpoints() == 2
    latest = mgr.get_latest_checkpoint("exec_100")
    assert latest is not None
    assert latest.checkpoint_id == chk2.checkpoint_id
    assert latest.step_index == 2

    all_chks = mgr.list_checkpoints("exec_100")
    assert len(all_chks) == 2


def test_checkpoint_manager_empty_id_error() -> None:
    """Verifies error handling when creating a checkpoint with empty execution_id."""
    mgr = CheckpointManager()
    with pytest.raises(CheckpointError):
        mgr.create_checkpoint("", CheckpointType.AUTOMATIC, {})


def test_state_store_saving_and_query() -> None:
    """Verifies StateStore snapshot saving and latest snapshot retrieval."""
    store = StateStore()

    snap1 = store.save_snapshot("exec_200", {"phase": 1}, SnapshotType.FULL)
    snap2 = store.save_snapshot("exec_200", {"phase": 2}, SnapshotType.DELTA)

    latest = store.get_latest_snapshot("exec_200")
    assert latest is not None
    assert latest.snapshot_id == snap2.snapshot_id
    assert latest.snapshot_type == SnapshotType.DELTA


def test_state_store_empty_id_error() -> None:
    """Verifies error handling when saving snapshot with empty execution_id."""
    store = StateStore()
    with pytest.raises(StateStoreError):
        store.save_snapshot("", {"key": "val"})


def test_recovery_engine_planning_and_execution() -> None:
    """Verifies RecoveryEngine plan generation and strategy execution."""
    mgr = CheckpointManager()
    chk = mgr.create_checkpoint("exec_300", CheckpointType.AUTOMATIC, {"data": "saved_state"})

    engine = RecoveryEngine(checkpoint_manager=mgr)

    plan = engine.plan_recovery("exec_300", strategy=RecoveryStrategy.RESUME_CHECKPOINT)
    assert plan.execution_id == "exec_300"
    assert plan.target_checkpoint_id == chk.checkpoint_id
    assert len(plan.steps) > 0

    execution = engine.execute_recovery(plan)
    assert execution.status == RecoveryStatus.SUCCESS
    assert execution.restored_state.get("data") == "saved_state"


def test_rollback_manager_planning_and_execution() -> None:
    """Verifies RollbackManager plan generation and step reversal execution."""
    mgr = CheckpointManager()
    chk = mgr.create_checkpoint("exec_400", CheckpointType.STAGE, {"stage": 1})

    rb_mgr = RollbackManager(checkpoint_manager=mgr)

    plan = rb_mgr.plan_rollback("exec_400", target_checkpoint_id=chk.checkpoint_id)
    assert plan.execution_id == "exec_400"
    assert plan.target_checkpoint_id == chk.checkpoint_id

    result = rb_mgr.execute_rollback(plan)
    assert result.status == RollbackStatus.COMPLETED
    assert result.reverted_steps == len(plan.rollback_steps)


def test_recovery_provider_end_to_end_and_health() -> None:
    """Verifies RecoveryProvider end-to-end checkpointing, recovery, rollback, health reporting, and statistics."""
    provider = RecoveryProvider()

    chk = provider.create_checkpoint("exec_500", {"var": 123}, checkpoint_type=CheckpointType.STEP)
    assert chk.execution_id == "exec_500"

    rec_res = provider.recover_execution("exec_500", strategy=RecoveryStrategy.RESUME_CHECKPOINT)
    assert rec_res.status == RecoveryStatus.SUCCESS

    rb_res = provider.rollback_execution("exec_500", target_checkpoint_id=chk.checkpoint_id)
    assert rb_res.status == RollbackStatus.COMPLETED

    health = provider.health_check()
    assert isinstance(health, RecoveryHealth)
    assert health.healthy is True
    assert len(health.components) == 4

    stats = provider.get_statistics()
    assert isinstance(stats, RecoveryStatistics)
    assert stats.total_checkpoints == 1
    assert stats.total_recoveries == 1
    assert stats.total_rollbacks == 1

    provider.clear()
    assert provider.get_statistics().total_checkpoints == 0


def test_recovery_runtime_lifecycle_and_singleton() -> None:
    """Verifies RecoveryRuntime initialization, status management, health reporting, and singleton accessors."""
    rt = get_recovery_runtime()
    assert rt.status == RecoveryRuntimeStatus.READY

    rt2 = get_recovery_runtime()
    assert rt is rt2

    chk = rt.create_checkpoint("exec_600", {"k": "v"})
    assert chk.execution_id == "exec_600"

    rec_res = rt.recover_execution("exec_600")
    assert rec_res.status == RecoveryStatus.SUCCESS

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_checkpoints == 1

    rt.clear()
    assert rt.get_statistics().total_checkpoints == 0

    assert rt.shutdown() is True
    assert rt.status == RecoveryRuntimeStatus.SHUTDOWN


def test_recovery_runtime_thread_safety() -> None:
    """Verifies thread-safe recovery and checkpoint operations across concurrent worker threads."""
    rt = get_recovery_runtime()

    def worker(i: int) -> str:
        chk = rt.create_checkpoint(f"exec_thread_{i}", {"thread": i})
        res = rt.recover_execution(f"exec_thread_{i}")
        return res.recovery_id

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, range(15)))

    assert len(results) == 15

    stats = rt.get_statistics()
    assert stats.total_checkpoints == 15
    assert stats.total_recoveries == 15
    assert stats.successful_recoveries == 15
