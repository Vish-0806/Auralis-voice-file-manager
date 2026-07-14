"""Unit tests for the Personalization Engine subsystem."""

from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest

from memory.personalization import (
    PersonalizationService,
    PersonalizationEngine,
    DecisionEngine,
    ProfileBuilder,
    RecommendationEngine,
    InvalidPersonalizationConfigError,
)


@pytest.fixture
def mock_preference_service():
    """Provides a mock PreferenceService."""
    service = MagicMock()

    def get_side_effect(user_id, category, key):
        return {
            "ide": {"theme": "light"},
            "voice": {"speech_rate": 160},
        }.get(category, {}).get(key)

    service.get.side_effect = get_side_effect
    service.list.side_effect = lambda user_id, category: {
        "ide": {"theme": "light"},
        "voice": {"speech_rate": 160},
    }.get(category, {})
    return service


@pytest.fixture
def mock_context_service():
    """Provides a mock ContextService."""
    service = MagicMock()
    service.load.return_value = {
        "active_workspace": "/projects/auralis",
        "shell": "bash",
    }
    return service


@pytest.fixture
def mock_workspace_service():
    """Provides a mock WorkspaceService."""
    service = MagicMock()
    # Mock workspace profile list
    w1 = MagicMock()
    w1.name = "My Coding Profile"
    w1.path = "/projects/auralis"
    w1.settings = {
        "theme": "ocean-dark",
        "env_vars": {"SHELL": "zsh"},
    }
    service.list.return_value = [w1]
    return service


@pytest.fixture
def mock_routine_service():
    """Provides a mock RoutineLearningService."""
    service = MagicMock()
    r1 = MagicMock()
    r1.id = 101
    r1.trigger_event = "OPEN_APPLICATION:VS Code"
    r1.confidence_score = 0.9
    r1.action_sequence = {
        "steps": [{"action": "OPEN_APPLICATION", "input_parameters": {"target": "VS Code"}}]
    }
    service.list.return_value = [r1]

    # Mock execution history repository access within service
    mock_history = MagicMock()
    mock_history.action = "OPEN_APPLICATION"
    mock_history.created_at = None
    service._engine._execution_repository.search.return_value = [mock_history]
    return service


@pytest.fixture
def personalization_service(
    mock_preference_service,
    mock_context_service,
    mock_workspace_service,
    mock_routine_service,
) -> PersonalizationService:
    """Provides a configured PersonalizationService using mocks."""
    engine = PersonalizationEngine(
        preference_service=mock_preference_service,
        context_service=mock_context_service,
        workspace_service=mock_workspace_service,
        routine_service=mock_routine_service,
    )
    return PersonalizationService(engine=engine)


def test_profile_builder_aggregates_correctly(personalization_service: PersonalizationService) -> None:
    """Verify ProfileBuilder merges context, preferences, and routines correctly."""
    user_id = 1
    session_id = "sess_1"

    profile = personalization_service.profile(user_id, session_id)
    assert profile.user_id == 1
    assert profile.active_workspace_path == "/projects/auralis"
    assert profile.preferences["ide"]["theme"] == "light"
    assert profile.active_routines_count == 1
    assert profile.recent_actions == ["OPEN_APPLICATION"]


def test_decision_engine_priority_ladder(personalization_service: PersonalizationService) -> None:
    """Verify conflict resolution adheres to the exact priority mapping sequence."""
    user_id = 1
    session_id = "sess_2"

    # Priority 1: Explicit Command Override
    overrides = {"theme": "purple"}
    ctx = personalization_service.context(user_id, session_id, user_overrides=overrides)
    assert ctx.resolved_settings["theme"] == "purple"
    assert ctx.source_mapping["theme"] == "Explicit User Command"

    # Priority 2: Context Value
    # 'shell' is present in context mock as 'bash'
    ctx_no_override = personalization_service.context(user_id, session_id)
    assert ctx_no_override.resolved_settings["shell"] == "bash"
    assert ctx_no_override.source_mapping["shell"] == "Current Context"

    # Priority 3: Workspace Profile
    # 'theme' is resolved from Workspace Settings ('ocean-dark') since there are no context or command overrides
    assert ctx_no_override.resolved_settings["theme"] == "ocean-dark"
    assert ctx_no_override.source_mapping["theme"] == "Workspace Profile"

    # Priority 4: User Preference
    # 'speech_rate' is resolved from mock_preference_service (160)
    assert ctx_no_override.resolved_settings["speech_rate"] == 160
    assert ctx_no_override.source_mapping["speech_rate"] == "User Preferences"

    # Priority 5: Learned Routine
    # 'editor' matches the VS Code app launch routine step
    assert ctx_no_override.resolved_settings["editor"] == "VS Code"
    assert ctx_no_override.source_mapping["editor"] == "Learned Routine"

    # Priority 6: Default (unresolved 'voice_provider')
    assert ctx_no_override.resolved_settings["voice_provider"] == "google"
    assert ctx_no_override.source_mapping["voice_provider"] == "System Defaults"


def test_recommendation_engine_signals(personalization_service: PersonalizationService) -> None:
    """Verify that recommendations trigger correctly based on path cues, times, and routines."""
    user_id = 1
    session_id = "sess_3"

    recs = personalization_service.recommendations(user_id, session_id)

    # Coding workspace switch should be recommended based on path '/projects/auralis'
    ws_recs = [r for r in recs if r.type == "workspace_restore"]
    assert len(ws_recs) == 1
    assert "My Coding Profile" in ws_recs[0].message

    # High confidence routine trigger recommended
    routine_recs = [r for r in recs if r.type == "routine_trigger"]
    assert len(routine_recs) == 1
    assert "OPEN_APPLICATION:VS Code" in routine_recs[0].message


def test_validator_detects_invalid_inputs(personalization_service: PersonalizationService) -> None:
    """Verify validator errors on bad user or session identifiers."""
    with pytest.raises(InvalidPersonalizationConfigError):
        personalization_service.profile(0, "sess_1")

    with pytest.raises(InvalidPersonalizationConfigError):
        personalization_service.profile(1, "   ")
