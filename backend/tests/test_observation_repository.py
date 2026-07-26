# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from memory.providers.base_provider import InMemoryProvider
from memory.workflows.workflow_models import WorkflowStepObservation, WorkflowSequence, WorkflowObservation
from memory.workflows.observation_repository import ObservationRepository


def create_mock_observation(user_id: int, execution_id: str, session_id: str = "session_1", offset_seconds: int = 0) -> WorkflowObservation:
    t = datetime.now(timezone.utc) - timedelta(seconds=offset_seconds)
    step = WorkflowStepObservation(
        step_id="step_1",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        timestamp=t
    )
    seq = WorkflowSequence(
        steps=[step],
        sequence_id=f"seq_{execution_id}",
        sequence_hash="hash",
        total_duration_ms=10.0
    )
    return WorkflowObservation(
        user_id=user_id,
        execution_id=execution_id,
        sequence=seq,
        success=True,
        timestamp=t,
        context_metadata={"session_id": session_id}
    )


@pytest.mark.anyio
async def test_observation_repository_crud():
    provider = InMemoryProvider()
    repo = ObservationRepository(provider)
    
    obs = create_mock_observation(user_id=1, execution_id="exec_1")
    
    # 1. Save and Get
    await repo.save(obs)
    retrieved = await repo.get("exec_1")
    assert retrieved is not None
    assert retrieved.user_id == 1
    assert retrieved.execution_id == "exec_1"
    
    # 2. Update
    obs.success = False
    await repo.save(obs)
    retrieved = await repo.get("exec_1")
    assert retrieved.success is False
    
    # 3. Delete
    await repo.delete("exec_1")
    retrieved = await repo.get("exec_1")
    assert retrieved is None


@pytest.mark.anyio
async def test_observation_repository_user_and_session_queries():
    provider = InMemoryProvider()
    repo = ObservationRepository(provider)
    
    obs1 = create_mock_observation(user_id=1, execution_id="exec_1", session_id="session_A")
    obs2 = create_mock_observation(user_id=1, execution_id="exec_2", session_id="session_B")
    obs3 = create_mock_observation(user_id=2, execution_id="exec_3", session_id="session_A")
    
    await repo.save(obs1)
    await repo.save(obs2)
    await repo.save(obs3)
    
    # Query by User
    user_1_obs = await repo.list_by_user(1)
    assert len(user_1_obs) == 2
    assert {o.execution_id for o in user_1_obs} == {"exec_1", "exec_2"}
    
    user_2_obs = await repo.list_by_user(2)
    assert len(user_2_obs) == 1
    assert user_2_obs[0].execution_id == "exec_3"
    
    # Query by Session
    session_a_obs = await repo.list_by_session("session_A")
    assert len(session_a_obs) == 2
    assert {o.execution_id for o in session_a_obs} == {"exec_1", "exec_3"}


@pytest.mark.anyio
async def test_observation_repository_cleanup():
    provider = InMemoryProvider()
    repo = ObservationRepository(provider)
    
    # Current time cutoff definition
    now = datetime.now(timezone.utc)
    
    # Old observations (2 hours ago)
    old_obs1 = create_mock_observation(user_id=1, execution_id="old_1", offset_seconds=7200)
    old_obs2 = create_mock_observation(user_id=1, execution_id="old_2", offset_seconds=7200)
    # New observation (recent)
    new_obs = create_mock_observation(user_id=1, execution_id="new_1", offset_seconds=0)
    
    await repo.save(old_obs1)
    await repo.save(old_obs2)
    await repo.save(new_obs)
    
    # Cleanup cutoff (1 hour ago)
    cutoff = now - timedelta(hours=1)
    deleted_count = await repo.cleanup(cutoff)
    
    assert deleted_count == 2
    assert await repo.get("old_1") is None
    assert await repo.get("old_2") is None
    assert await repo.get("new_1") is not None


@pytest.mark.anyio
async def test_observation_repository_empty_behavior():
    provider = InMemoryProvider()
    repo = ObservationRepository(provider)
    
    assert await repo.get("non-existent") is None
    assert await repo.list_by_user(999) == []
    assert await repo.list_by_session("non-existent") == []
    assert await repo.cleanup(datetime.now(timezone.utc)) == 0
