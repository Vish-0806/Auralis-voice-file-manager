# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, Session
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.compiler import compiles
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB

from memory.database import Base
from memory.models.domain_models import UserDomain
from memory.repository.user_repository import UserRepository
from memory.repository.proactive_recommendation_repository import ProactiveRecommendationRepository
from memory.proactive import (
    ProactiveRecommendationDomain,
    PredictionContext,
    ActivityPredictor,
    RecommendationEngine,
    RecommendationScoringEngine,
    RecommendationPrioritizer,
    SuggestionHistoryManager,
    UserFeedbackEngine,
    ProactiveAssistantCoordinator,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite_proactive(type_, compiler, **kw):
    """Compiles JSONB as JSON under SQLite to support test suites."""
    return "JSON"


@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLite in-memory engine for proactive testing."""
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


def test_activity_predictor():
    predictor = ActivityPredictor()

    class DummyExecution:
        def __init__(self, action):
            self.action = action

    class DummyRoutine:
        def __init__(self, trigger, steps):
            self.trigger_condition = {"trigger_event": trigger}
            self.steps = steps

    # Context with executions matching routines sequence
    context = PredictionContext(
        executions=[DummyExecution("OPEN_APPLICATION")],
        routines=[DummyRoutine("OPEN_APPLICATION", [{"action": "SET_VOLUME"}, {"action": "MUTE"}])],
        workspace_info={"project_type": "python", "repository_type": "git"},
        preferences={"preferred_automation": True}
    )

    predicted = predictor.predict_next_actions(context)
    # Checks that next actions from routines and workspace detections are returned
    assert "SET_VOLUME" in predicted
    assert "MUTE" in predicted
    assert "COMPILE_PROJECT" in predicted
    assert "RUN_COMMAND" in predicted


def test_recommendation_engine():
    engine = RecommendationEngine()
    context = PredictionContext(
        workspace_info={"workspace_path": "C:/Projects/Auralis"},
        executions=[1]
    )

    recs = engine.generate_recommendations(
        user_id=1,
        predicted_actions=["OPEN_APPLICATION", "RUN_COMMAND"],
        context=context
    )

    assert len(recs) == 5
    texts = [r.suggestion_text for r in recs]
    assert "Open VS Code?" in texts
    assert "Run Git Pull?" in texts
    assert "Resume previous workspace?" in texts
    assert "Continue yesterday's work?" in texts


def test_scoring_engine():
    scorer = RecommendationScoringEngine()
    context = PredictionContext(
        workspace_info={"workspace_path": "C:/Projects/Auralis", "repository_type": "git"}
    )

    r1 = ProactiveRecommendationDomain(
        user_id=1,
        suggestion_text="Run Git Pull?",
        action_type="RUN_COMMAND",
        scoring_details={"source": "git_repository"}
    )

    scored = scorer.score_recommendations([r1], context, feedback_weights={"RUN_COMMAND": 1.2})
    assert len(scored) == 1
    rec = scored[0]
    assert rec.confidence_score > 0.5
    assert rec.scoring_details["feedback_multiplier"] == 1.2


def test_prioritizer():
    prioritizer = RecommendationPrioritizer()

    r1 = ProactiveRecommendationDomain(
        user_id=1, suggestion_text="Suggest A", action_type="A", confidence_score=0.8
    )
    r2 = ProactiveRecommendationDomain(
        user_id=1, suggestion_text="Suggest B", action_type="B", confidence_score=0.9
    )
    r3 = ProactiveRecommendationDomain(
        user_id=1, suggestion_text="Suggest A", action_type="A", confidence_score=0.5
    )

    prioritized = prioritizer.prioritize([r1, r2, r3], limit=2)
    assert len(prioritized) == 2
    assert prioritized[0].suggestion_text == "Suggest B"
    assert prioritized[1].suggestion_text == "Suggest A"


def test_feedback_engine():
    engine = UserFeedbackEngine()

    r1 = ProactiveRecommendationDomain(
        user_id=1, suggestion_text="A", action_type="RUN_COMMAND", status="accepted"
    )
    r2 = ProactiveRecommendationDomain(
        user_id=1, suggestion_text="B", action_type="RUN_COMMAND", status="accepted"
    )
    r3 = ProactiveRecommendationDomain(
        user_id=1, suggestion_text="C", action_type="OPEN_APPLICATION", status="dismissed"
    )

    weights = engine.compute_feedback_weights([r1, r2, r3])
    # accepted increases weight (+0.15 * 2) -> 1.3
    assert weights["RUN_COMMAND"] == 1.3
    # dismissed decreases weight (-0.25) -> 0.75
    assert weights["OPEN_APPLICATION"] == 0.75


def test_recommendation_repository_crud(db_session: Session) -> None:
    user_repo = UserRepository(db_session)
    rec_repo = ProactiveRecommendationRepository(db_session)

    user = user_repo.create(UserDomain(username="proactive_user"))

    domain = ProactiveRecommendationDomain(
        user_id=user.id,
        suggestion_text="Resume Auralis workspace?",
        action_type="OPEN_WORKSPACE",
        scoring_details={"source": "history"}
    )

    # 1. Create
    saved = rec_repo.create(domain)
    assert saved.id is not None
    assert saved.suggestion_text == "Resume Auralis workspace?"

    # 2. Read
    retrieved = rec_repo.get_by_id(saved.id)
    assert retrieved.id == saved.id
    assert retrieved.action_type == "OPEN_WORKSPACE"

    # 3. Update
    retrieved.status = "accepted"
    updated = rec_repo.update(saved.id, retrieved)
    assert updated.status == "accepted"

    # 4. Search
    results = rec_repo.search({"status": "accepted"})
    assert len(results) == 1

    # 5. Delete
    assert rec_repo.delete(saved.id) is True
    assert rec_repo.get_by_id(saved.id) is None


def test_coordinator_e2e_flow(db_session: Session) -> None:
    user_repo = UserRepository(db_session)
    rec_repo = ProactiveRecommendationRepository(db_session)

    user = user_repo.create(UserDomain(username="proactive_coordinator_user"))

    predictor = ActivityPredictor()
    engine = RecommendationEngine()
    scorer = RecommendationScoringEngine()
    prioritizer = RecommendationPrioritizer()
    history_manager = SuggestionHistoryManager(rec_repo)
    feedback_engine = UserFeedbackEngine()

    coordinator = ProactiveAssistantCoordinator(
        predictor=predictor,
        engine=engine,
        scorer=scorer,
        prioritizer=prioritizer,
        history_manager=history_manager,
        feedback_engine=feedback_engine
    )

    context = PredictionContext(
        workspace_info={"workspace_path": "C:/Projects/Auralis", "repository_type": "git"}
    )

    # Run complete workflow
    recs = coordinator.generate_proactive_recommendations(user.id, context)
    assert len(recs) > 0
    assert recs[0].user_id == user.id
    assert recs[0].confidence_score > 0.0

    # Ensure suggestions are persisted
    history = coordinator.history_manager.get_history(user.id)
    assert len(history) == len(recs)
