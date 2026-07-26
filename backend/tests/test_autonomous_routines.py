# pyrefly: ignore [missing-import]
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.models.domain_models import UserDomain
from memory.repository.user_repository import UserRepository
from memory.repository.routine_definition_repository import RoutineDefinitionRepository
from memory.routines import (
    RoutineCandidate,
    RoutineDefinitionDomain,
    RoutinePatternDetector,
    RoutineValidator,
    RoutineOptimizer,
    RoutineLibrary,
    RoutineMatcher,
    RoutineScheduler,
    RoutineRuntimeMonitor,
    RoutineLearningCoordinator,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite_routines(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLite in-memory engine for routines testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Session:
    """Provides a transactional database Session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_local = sessionmaker(bind=connection)
    session = session_local()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


def test_pattern_detector():
    detector = RoutinePatternDetector(min_support=2, min_confidence=0.5)

    class DummyExecution:
        def __init__(self, action, created_at):
            self.action = action
            self.created_at = created_at

    now = datetime.now(timezone.utc)
    executions = [
        DummyExecution("OPEN_APPLICATION", now),
        DummyExecution("SET_VOLUME", now + timedelta(seconds=10)),
        DummyExecution("OPEN_APPLICATION", now + timedelta(seconds=60)),
        DummyExecution("SET_VOLUME", now + timedelta(seconds=70)),
    ]

    candidates = detector.detect_candidates(executions)
    assert len(candidates) > 0
    candidate = candidates[0]
    assert candidate.trigger_event == "OPEN_APPLICATION"
    assert candidate.action_sequence["steps"][0]["action"] == "SET_VOLUME"
    assert candidate.frequency == 2
    assert candidate.confidence_score == 1.0


def test_validator():
    validator = RoutineValidator()

    # Valid candidate
    c1 = RoutineCandidate(
        trigger_event="OPEN_APPLICATION",
        action_sequence={"steps": [{"action": "SET_VOLUME", "parameters": {}}]},
        confidence_score=0.9
    )
    assert validator.validate_routine(c1) is True

    # Invalid: unsupported capability
    c2 = RoutineCandidate(
        trigger_event="OPEN_APPLICATION",
        action_sequence={"steps": [{"action": "NON_EXISTENT_INTENT", "parameters": {}}]},
        confidence_score=0.9
    )
    assert validator.validate_routine(c2) is False

    # Invalid: conflicting intents
    c3 = RoutineCandidate(
        trigger_event="OPEN_APPLICATION",
        action_sequence={"steps": [{"action": "MUTE"}, {"action": "SET_VOLUME"}]},
        confidence_score=0.9
    )
    assert validator.validate_routine(c3) is False

    # Invalid: circular dependency (duplicate actions in sequence)
    c4 = RoutineCandidate(
        trigger_event="OPEN_APPLICATION",
        action_sequence={"steps": [{"action": "MUTE"}, {"action": "MUTE"}]},
        confidence_score=0.9
    )
    assert validator.validate_routine(c4) is False

    # Safety check: SHUTDOWN triggers user approval flag
    c5 = RoutineCandidate(
        trigger_event="OPEN_APPLICATION",
        action_sequence={"steps": [{"action": "SHUTDOWN"}]},
        confidence_score=0.9
    )
    assert validator.requires_user_approval(c5) is True


def test_optimizer():
    optimizer = RoutineOptimizer()

    steps = [
        {"action": "OPEN_APPLICATION", "parameters": {"target": "VS Code", "extra": None}},
        {"action": "OPEN_APPLICATION", "parameters": {"target": "VS Code", "extra": ""}},
        {"action": "SET_VOLUME", "parameters": {"level": 50}}
    ]

    optimised, report = optimizer.optimize_sequence(steps)
    assert report.original_steps_count == 3
    assert report.optimised_steps_count == 2  # duplicate removed
    assert report.estimated_runtime_reduction_ms == 200.0

    # Ensure parameters are pruned
    assert "extra" not in optimised[0]["parameters"]
    assert optimised[0]["execution_group"] == 1


def test_matcher():
    matcher = RoutineMatcher()

    r1 = RoutineDefinitionDomain(
        user_id=1,
        name="Developer Workspace Setup",
        steps=[{"action": "OPEN_APPLICATION", "parameters": {"target": "VS Code"}}],
        trigger_condition={"trigger_event": "WorkspaceOpened"},
        metadata_info={"tags": ["coding", "dev"]}
    )

    r2 = RoutineDefinitionDomain(
        user_id=1,
        name="Evening Relaxation Setup",
        steps=[{"action": "SET_VOLUME", "parameters": {"level": 10}}],
        trigger_condition={"trigger_event": "EveningTime"},
        metadata_info={"tags": ["relax"]}
    )

    routines = [r1, r2]

    # Tag search match
    matches = matcher.match_routines("Evening relax schedule", routines)
    assert len(matches) == 1
    assert matches[0].name == "Evening Relaxation Setup"

    # Name search match
    matches = matcher.match_routines("open developer Workspace", routines)
    assert len(matches) == 1
    assert matches[0].name == "Developer Workspace Setup"


@pytest.mark.anyio
async def test_scheduler():
    scheduler = RoutineScheduler()
    called_list = []

    def dummy_callback(routine):
        called_list.append(routine)

    # 1. Delayed scheduling execution
    scheduler.schedule_delayed("test_delayed", delay_seconds=0.1, callback=dummy_callback)
    await asyncio.sleep(0.2)
    assert len(called_list) == 1
    assert called_list[0] == "test_delayed"

    # 2. Startup / Shutdown registers
    scheduler.register_startup_routine("start_rt")
    scheduler.register_shutdown_routine("stop_rt")

    called_startup = []
    await scheduler.execute_startup_routines(callback=lambda r: called_startup.append(r))
    assert called_startup == ["start_rt"]

    called_shutdown = []
    await scheduler.execute_shutdown_routines(callback=lambda r: called_shutdown.append(r))
    assert called_shutdown == ["stop_rt"]


def test_runtime_monitor():
    monitor = RoutineRuntimeMonitor()

    monitor.record_execution(routine_id=10, duration_ms=400.0, success=True)
    monitor.record_execution(routine_id=10, duration_ms=600.0, success=False)
    monitor.record_execution(routine_id=10, duration_ms=500.0, success=True)

    stats = monitor.get_statistics(routine_id=10)
    assert stats["total_runs"] == 3
    assert pytest.approx(stats["success_rate"], 0.01) == 0.67
    assert stats["avg_duration_ms"] == 500.0
    assert stats["failures_count"] == 1
    assert len(stats["optimisation_opportunities"]) > 0  # low success rate warning


def test_routine_repository_crud(db_session: Session) -> None:
    user_repo = UserRepository(db_session)
    routine_repo = RoutineDefinitionRepository(db_session)

    user = user_repo.create(UserDomain(username="routine_definition_user"))

    domain = RoutineDefinitionDomain(
        user_id=user.id,
        name="Build Script Automations",
        description="Initial build sequence",
        steps=[{"action": "OPEN_APPLICATION", "parameters": {"target": "Terminal"}}],
        trigger_condition={"trigger_event": "BuildStart"}
    )

    # 1. Create
    saved = routine_repo.create(domain)
    assert saved.id is not None
    assert saved.name == "Build Script Automations"

    # 2. Read
    retrieved = routine_repo.get_by_id(saved.id)
    assert retrieved.id == saved.id
    assert retrieved.steps[0]["action"] == "OPEN_APPLICATION"

    # 3. Update
    retrieved.name = "Updated Build Automations"
    updated = routine_repo.update(saved.id, retrieved)
    assert updated.name == "Updated Build Automations"

    # 4. Search
    results = routine_repo.search({"name": "Updated Build Automations"})
    assert len(results) == 1

    # 5. Delete
    assert routine_repo.delete(saved.id) is True
    assert routine_repo.get_by_id(saved.id) is None


def test_coordinator_e2e_flow(db_session: Session) -> None:
    user_repo = UserRepository(db_session)
    routine_repo = RoutineDefinitionRepository(db_session)

    user = user_repo.create(UserDomain(username="coordinator_user"))

    # Initialize sub-components
    detector = RoutinePatternDetector(min_support=2, min_confidence=0.5)
    validator = RoutineValidator()
    optimizer = RoutineOptimizer()
    library = RoutineLibrary(routine_repo)
    matcher = RoutineMatcher()
    scheduler = RoutineScheduler()
    monitor = RoutineRuntimeMonitor()

    coordinator = RoutineLearningCoordinator(
        pattern_detector=detector,
        validator=validator,
        optimizer=optimizer,
        library=library,
        matcher=matcher,
        scheduler=scheduler,
        monitor=monitor
    )

    class DummyExecution:
        def __init__(self, action, created_at):
            self.action = action
            self.created_at = created_at

    now = datetime.now(timezone.utc)
    executions = [
        DummyExecution("OPEN_APPLICATION", now),
        DummyExecution("SET_VOLUME", now + timedelta(seconds=10)),
        DummyExecution("OPEN_APPLICATION", now + timedelta(seconds=60)),
        DummyExecution("SET_VOLUME", now + timedelta(seconds=70)),
    ]

    # Process logs and discover candidates
    candidates = coordinator.process_execution_history(user.id, executions)
    assert len(candidates) == 1

    # Promote candidate to library definition
    promoted = coordinator.promote_candidate(user.id, candidates[0], name="Promoted Routine A")
    assert promoted is not None
    assert promoted.id is not None
    assert promoted.name == "Promoted Routine A"
    assert promoted.trigger_condition["trigger_event"] == "OPEN_APPLICATION"

    # Verify query matching
    matches = coordinator.matcher.match_routines("open application script", coordinator.library.list_routines())
    assert len(matches) == 1
    assert matches[0].name == "Promoted Routine A"
