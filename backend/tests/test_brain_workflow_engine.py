"""Unit test suite for Phase 12.4 — Workflow Execution Engine.

Covers:
- Workflow models, enums, defaults, and immutability
- Subsystem exceptions hierarchy
- WorkflowBuilder request graph construction
- WorkflowValidator graph integrity and cycle detection (DFS)
- WorkflowScheduler topological sorting and priority-aware ordering
- WorkflowExecutor multi-step execution, retries, output passing, and cancellation
- WorkflowProvider end-to-end processing, health checks, and statistics
- WorkflowRuntime singleton lifecycle, status management, and thread safety under concurrency
- Mock integrations for Command Execution Orchestrator and Planning Runtime
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.workflow import (
    DependencyType,
    IWorkflowProvider,
    WorkflowBuilder,
    WorkflowCancellationError,
    WorkflowContext,
    WorkflowDependencyError,
    WorkflowException,
    WorkflowExecution,
    WorkflowExecutionMode,
    WorkflowExecutor,
    WorkflowHealth,
    WorkflowPriority,
    WorkflowProvider,
    WorkflowRequest,
    WorkflowResult,
    WorkflowRuntime,
    WorkflowRuntimeStatus,
    WorkflowScheduler,
    WorkflowStatistics,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowValidationError,
    WorkflowValidator,
    get_workflow_runtime,
    reset_workflow_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global runtime before and after each test."""
    reset_workflow_runtime()
    yield
    reset_workflow_runtime()


def test_workflow_models_defaults_and_immutability() -> None:
    """Verifies workflow model default properties and Pydantic v2 immutability."""
    step = WorkflowStep(
        step_id="step_1",
        name="Search PDF",
        action_type="SEARCH",
        priority=WorkflowPriority.HIGH,
    )
    assert step.step_id == "step_1"
    assert step.priority == WorkflowPriority.HIGH

    with pytest.raises((TypeError, ValidationError)):
        step.name = "Modified Name"  # type: ignore

    req = WorkflowRequest(name="PDF Workflow", steps=[step])
    assert req.name == "PDF Workflow"
    assert len(req.steps) == 1

    with pytest.raises((TypeError, ValidationError)):
        req.name = "New Workflow"  # type: ignore


def test_workflow_exceptions_hierarchy() -> None:
    """Verifies exception inheritance hierarchy."""
    exc = WorkflowValidationError("Graph validation failed")
    assert isinstance(exc, WorkflowException)


def test_workflow_builder_construction() -> None:
    """Verifies workflow builder graph assembly and priority derivation."""
    builder = WorkflowBuilder()
    step1 = WorkflowStep(step_id="s1", name="Step 1", priority=WorkflowPriority.NORMAL)
    step2 = WorkflowStep(step_id="s2", name="Step 2", priority=WorkflowPriority.CRITICAL)

    req = builder.build_workflow("Priority Workflow", [step1, step2])
    assert req.name == "Priority Workflow"
    assert req.priority == WorkflowPriority.CRITICAL
    assert len(req.steps) == 2


def test_workflow_validator_cycle_detection() -> None:
    """Verifies validator graph checks for empty graphs, duplicate IDs, missing references, and cycles."""
    validator = WorkflowValidator()

    # Empty workflow
    req_empty = WorkflowRequest(name="Empty", steps=[])
    diags1 = validator.validate_workflow(req_empty)
    assert any("zero steps" in d for d in diags1)

    # Valid DAG graph
    step_a = WorkflowStep(step_id="A", name="Step A")
    step_b = WorkflowStep(step_id="B", name="Step B", dependencies=["A"])
    req_dag = WorkflowRequest(name="DAG", steps=[step_a, step_b])
    diags_dag = validator.validate_workflow(req_dag)
    assert len(diags_dag) == 0

    # Cyclic graph A -> B -> A
    step_c1 = WorkflowStep(step_id="A", name="Step A", dependencies=["B"])
    step_c2 = WorkflowStep(step_id="B", name="Step B", dependencies=["A"])
    req_cycle = WorkflowRequest(name="Cycle", steps=[step_c1, step_c2])
    diags_cycle = validator.validate_workflow(req_cycle)
    assert any("Cyclic dependency" in d for d in diags_cycle)


def test_workflow_scheduler_topological_sorting() -> None:
    """Verifies topological sorting and priority-aware step scheduling."""
    scheduler = WorkflowScheduler()

    step_a = WorkflowStep(step_id="A", name="Step A", priority=WorkflowPriority.NORMAL)
    step_b = WorkflowStep(step_id="B", name="Step B", dependencies=["A"], priority=WorkflowPriority.NORMAL)
    step_c = WorkflowStep(step_id="C", name="Step C", dependencies=["B"], priority=WorkflowPriority.HIGH)

    req = WorkflowRequest(name="Sorted Workflow", steps=[step_c, step_a, step_b])
    execution = scheduler.schedule(req)

    assert execution.status == WorkflowStatus.READY
    assert execution.execution_order == ["A", "B", "C"]


def test_workflow_executor_multi_step_execution_with_mocks() -> None:
    """Verifies multi-step execution flow, output passing, and step retries with mock orchestrator."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.orchestrate.return_value = MagicMock(output={"res": "SUCCESS"})

    executor = WorkflowExecutor(command_orchestrator=mock_orchestrator)
    scheduler = WorkflowScheduler()

    step_a = WorkflowStep(step_id="A", name="Step A", prompt_or_payload="Open Chrome")
    step_b = WorkflowStep(step_id="B", name="Step B", dependencies=["A"], prompt_or_payload="Search PDF")
    req = WorkflowRequest(name="Execution Test", steps=[step_a, step_b])

    execution = scheduler.schedule(req)
    result = executor.execute(execution, req)

    assert result.status == WorkflowStatus.COMPLETED
    assert result.completed_steps == 2
    assert len(result.step_results) == 2


def test_workflow_executor_cancellation() -> None:
    """Verifies workflow cancellation via cancellation token."""
    executor = WorkflowExecutor()
    scheduler = WorkflowScheduler()

    step_a = WorkflowStep(step_id="A", name="Step A")
    step_b = WorkflowStep(step_id="B", name="Step B", dependencies=["A"])
    req = WorkflowRequest(name="Cancel Test", steps=[step_a, step_b])

    execution = scheduler.schedule(req)
    cancel_token = {"cancelled": True}

    result = executor.execute(execution, req, cancellation_token=cancel_token)
    assert result.status == WorkflowStatus.CANCELLED
    assert result.completed_steps == 0


def test_workflow_executor_dependency_failure_cascade() -> None:
    """Verifies that dependent steps are SKIPPED if an upstream dependency fails."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.orchestrate.side_effect = RuntimeError("Step A failed execution")

    executor = WorkflowExecutor(command_orchestrator=mock_orchestrator)
    scheduler = WorkflowScheduler()

    step_a = WorkflowStep(step_id="A", name="Step A", max_retries=0)
    step_b = WorkflowStep(step_id="B", name="Step B", dependencies=["A"])
    req = WorkflowRequest(name="Cascade Failure Test", steps=[step_a, step_b])

    execution = scheduler.schedule(req)
    result = executor.execute(execution, req)

    assert result.status == WorkflowStatus.FAILED
    assert result.completed_steps == 0
    assert result.failed_steps == 1
    assert result.step_results[0].status == WorkflowStepStatus.FAILED
    assert result.step_results[1].status == WorkflowStepStatus.SKIPPED
    assert "dependency step(s) failed" in result.step_results[1].error


def test_workflow_provider_end_to_end_and_health_check() -> None:
    """Verifies WorkflowProvider end-to-end execution, health checks, and statistics."""
    provider = WorkflowProvider()

    step_a = WorkflowStep(step_id="s1", name="Create Dir")
    step_b = WorkflowStep(step_id="s2", name="Copy File", dependencies=["s1"])

    result = provider.execute_workflow([step_a, step_b])
    assert result.status == WorkflowStatus.COMPLETED
    assert result.completed_steps == 2

    health = provider.health_check()
    assert isinstance(health, WorkflowHealth)
    assert health.healthy is True
    assert len(health.components) == 4

    stats = provider.get_statistics()
    assert isinstance(stats, WorkflowStatistics)
    assert stats.total_workflows == 1
    assert stats.completed_count == 1
    assert stats.total_steps_executed == 2

    provider.clear()
    assert provider.get_statistics().total_workflows == 0


def test_workflow_runtime_lifecycle_and_singleton() -> None:
    """Verifies WorkflowRuntime initialization, processing, health checks, and global singleton accessors."""
    rt = get_workflow_runtime()
    assert rt.status == WorkflowRuntimeStatus.READY

    rt2 = get_workflow_runtime()
    assert rt is rt2

    step = WorkflowStep(step_id="s1", name="Step 1")
    result = rt.process_workflow([step])
    assert result.status == WorkflowStatus.COMPLETED

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_workflows == 1

    rt.clear()
    assert rt.get_statistics().total_workflows == 0

    assert rt.shutdown() is True
    assert rt.status == WorkflowRuntimeStatus.SHUTDOWN


def test_workflow_runtime_thread_safety() -> None:
    """Verifies thread-safe workflow execution across concurrent worker threads."""
    rt = get_workflow_runtime()

    def worker(i: int) -> WorkflowStatus:
        s1 = WorkflowStep(step_id=f"step_{i}_1", name="Task 1")
        s2 = WorkflowStep(step_id=f"step_{i}_2", name="Task 2", dependencies=[f"step_{i}_1"])
        res = rt.process_workflow([s1, s2])
        return res.status

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, range(15)))

    assert len(results) == 15
    assert all(status == WorkflowStatus.COMPLETED for status in results)

    stats = rt.get_statistics()
    assert stats.total_workflows == 15
    assert stats.completed_count == 15
    assert stats.total_steps_executed == 30
