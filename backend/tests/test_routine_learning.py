"""Unit tests for the Routine Learning subsystem."""

import time
# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.repository.routine_repository import RoutineRepository
from memory.repository.execution_repository import ExecutionRepository
from memory.learning import (
    RoutineLearningService,
    RoutineLearningEngine,
    PatternAnalyzer,
    ConfidenceCalculator,
    LearningValidator,
    LearningScheduler,
    RoutineSuggestion,
    InvalidRoutineError,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLite in-memory engine for routine learning testing."""
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


@pytest.fixture
def learning_engine(db_session: Session) -> RoutineLearningEngine:
    """Fixture providing a RoutineLearningEngine."""
    routine_repo = RoutineRepository(db_session)
    exec_repo = ExecutionRepository(db_session)
    return RoutineLearningEngine(routine_repository=routine_repo, execution_repository=exec_repo)


@pytest.fixture
def learning_service(learning_engine) -> RoutineLearningService:
    """Fixture providing a RoutineLearningService."""
    return RoutineLearningService(engine=learning_engine)


def test_confidence_calculator() -> None:
    """Verify confidence score calculations."""
    calc = ConfidenceCalculator()

    # Zero sessions
    assert calc.calculate(2, 0, 1.0) == 0.0

    # Low support scaling (min 3 sessions limit)
    assert calc.calculate(1, 1, 1.0) == 0.33  # 1 / 3 * 1.0
    assert calc.calculate(2, 2, 1.0) == 0.67  # 2 / 3 * 1.0

    # Normal calculation
    assert calc.calculate(4, 5, 0.8) == 0.64  # (4 / 5) * 0.8 = 0.64
    assert calc.calculate(10, 10, 1.0) == 1.0


def test_validator_detects_bad_routine_format() -> None:
    """Verify LearningValidator catches bad schema setups."""
    val = LearningValidator()

    # Empty trigger
    with pytest.raises(InvalidRoutineError):
        val.validate_routine("", {"steps": [{"action": "test"}]}, 0.5)

    # Empty action sequence
    with pytest.raises(InvalidWorkspaceError if "Workspace" in str(InvalidRoutineError) else InvalidRoutineError):
        val.validate_routine("trigger", {}, 0.5)

    # Empty steps list
    with pytest.raises(InvalidWorkspaceError if "Workspace" in str(InvalidRoutineError) else InvalidRoutineError):
        val.validate_routine("trigger", {"steps": []}, 0.5)

    # Missing action name
    with pytest.raises(InvalidWorkspaceError if "Workspace" in str(InvalidRoutineError) else InvalidRoutineError):
        val.validate_routine("trigger", {"steps": [{"input_parameters": {}}]}, 0.5)

    # Invalid confidence range
    with pytest.raises(InvalidWorkspaceError if "Workspace" in str(InvalidRoutineError) else InvalidRoutineError):
        val.validate_routine("trigger", {"steps": [{"action": "click"}]}, 1.5)


def test_pattern_analyzer_creates_episodes() -> None:
    """Verify pattern episodes grouping logic."""
    from memory.models.domain_models import ExecutionHistoryDomain

    base_time = datetime.now()
    ex1 = ExecutionHistoryDomain(user_id=1, action="A", status="success", created_at=base_time)
    ex2 = ExecutionHistoryDomain(user_id=1, action="B", status="success", created_at=base_time + timedelta(seconds=60))
    # ex3 exceeds the 300 seconds gap
    ex3 = ExecutionHistoryDomain(user_id=1, action="C", status="success", created_at=base_time + timedelta(seconds=400))
    ex4 = ExecutionHistoryDomain(user_id=1, action="D", status="success", created_at=base_time + timedelta(seconds=460))

    episodes = PatternAnalyzer._create_episodes([ex1, ex2, ex3, ex4])
    assert len(episodes) == 2
    assert len(episodes[0]) == 2
    assert len(episodes[1]) == 2


def test_routine_learning_flow(learning_service: RoutineLearningService, db_session: Session) -> None:
    """Verify recording executions, generating suggestions, muting, and accepting/deleting routines."""
    user_id = 20
    base_time = datetime.now()

    # 1. Populate recurring execution sequences (e.g. VS Code followed by Terminal, 3 times)
    # Episode 1
    t1 = base_time
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "VS Code"}, "success")
    # Tweak execution timestamp directly to support pattern grouping
    db_session.query(Base.metadata.tables["execution_history"]).update({"created_at": t1})
    db_session.commit()

    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "Terminal"}, "success")
    # Set second action within 60s
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(action="OPEN_APPLICATION", id=2).update(
        {"created_at": t1 + timedelta(seconds=60)}
    )
    db_session.commit()

    # Episode 2 (30 minutes later)
    t2 = base_time + timedelta(minutes=30)
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "VS Code"}, "success")
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=3).update({"created_at": t2})
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "Terminal"}, "success")
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=4).update({"created_at": t2 + timedelta(seconds=60)})
    db_session.commit()

    # Episode 3 (60 minutes later)
    t3 = base_time + timedelta(minutes=60)
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "VS Code"}, "success")
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=5).update({"created_at": t3})
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "Terminal"}, "success")
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=6).update({"created_at": t3 + timedelta(seconds=60)})
    db_session.commit()

    # 2. Analyze history and generate suggestions
    suggestions = learning_service.analyze(user_id, min_confidence=0.3)
    assert len(suggestions) == 1
    sugg = suggestions[0]
    assert sugg.trigger_event == "OPEN_APPLICATION:VS Code"
    assert sugg.action_sequence == {"steps": [{"action": "OPEN_APPLICATION", "input_parameters": {"target": "Terminal"}}]}
    assert sugg.confidence_score >= 0.8  # 3/3 sessions = 1.0 confidence

    # 3. Accept suggestion
    routine = learning_service.accept(user_id, sugg)
    assert routine.id is not None
    assert routine.trigger_event == "OPEN_APPLICATION:VS Code"

    # Confirm it shows up in active routines list
    routines = learning_service.list(user_id)
    assert len(routines) == 1
    assert routines[0].id == routine.id

    # 4. Suggestions should now exclude the accepted routine
    assert len(learning_service.analyze(user_id, min_confidence=0.3)) == 0

    # 5. Delete routine
    assert learning_service.delete(user_id, routine.id) is True
    assert len(learning_service.list(user_id)) == 0


def test_routine_learning_reject_suggestion(learning_service: RoutineLearningService, db_session: Session) -> None:
    """Verify that rejecting a suggestion prevents recommending it again."""
    user_id = 21
    base_time = datetime.now()

    # Create pattern (2 repeats)
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "Browser"}, "success")
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "Slack"}, "success")
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=7).update({"created_at": base_time})
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=8).update({"created_at": base_time + timedelta(seconds=60)})
    db_session.commit()

    t2 = base_time + timedelta(minutes=30)
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "Browser"}, "success")
    learning_service.record(user_id, "OPEN_APPLICATION", {"target": "Slack"}, "success")
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=9).update({"created_at": t2})
    db_session.query(Base.metadata.tables["execution_history"]).filter_by(id=10).update({"created_at": t2 + timedelta(seconds=60)})
    db_session.commit()

    # Analyze suggestion
    suggestions = learning_service.analyze(user_id, min_confidence=0.1)
    assert len(suggestions) == 1
    trigger = suggestions[0].trigger_event
    assert trigger == "OPEN_APPLICATION:Browser"

    # Reject suggestion
    learning_service.reject(user_id, trigger)

    # Next run should find 0 suggestions because it is muted
    assert len(learning_service.analyze(user_id, min_confidence=0.1)) == 0


def test_learning_scheduler_start_stop() -> None:
    """Verify scheduler triggers execution and stops cleanly."""
    called = []
    def callback():
        called.append(True)

    scheduler = LearningScheduler(callback=callback, interval_seconds=0.1)
    assert scheduler.is_running is False

    scheduler.start()
    assert scheduler.is_running is True

    # Allow time to execute callback
    time.sleep(0.15)
    scheduler.stop()

    assert scheduler.is_running is False
    assert len(called) >= 1
