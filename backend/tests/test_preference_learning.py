# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from memory.models.domain_models import MemoryEntry, MemoryMetadata, MemoryType
from memory.preferences.preference_learning import (
    PreferenceObservation,
    PreferenceCandidate,
    ResolvedPreference,
    PreferenceStatistics,
    PreferenceScorer,
    PreferenceLearner,
    PreferenceConflictResolver,
    PreferenceLearningCoordinator,
    ensure_utc,
)

def test_timezone_handling():
    # Test ensure_utc helper
    dt_naive = datetime(2026, 7, 26, 12, 0, 0)
    dt_aware = ensure_utc(dt_naive)
    assert dt_aware.tzinfo == timezone.utc

    dt_est = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
    dt_aware_est = ensure_utc(dt_est)
    assert dt_aware_est.tzinfo == timezone.utc
    assert dt_aware_est.hour == 17  # 12:00 EST is 17:00 UTC

    # Test Pydantic model validation on timezone aware fields
    obs = PreferenceObservation(
        user_id=1,
        category="Shell",
        value="PowerShell",
        timestamp=dt_naive
    )
    assert obs.timestamp.tzinfo == timezone.utc

def test_pydantic_serialization():
    obs = PreferenceObservation(
        user_id=1,
        category="Shell",
        value="PowerShell",
        timestamp=datetime.now(timezone.utc),
        is_override=True,
        execution_id="exec_1",
        execution_status="success",
        context_metadata={"os": "windows"}
    )
    
    # Serialize to dictionary and dump/load
    dumped = obs.model_dump()
    assert dumped["user_id"] == 1
    assert dumped["is_override"] is True
    assert dumped["context_metadata"]["os"] == "windows"

    # De-serialize
    loaded = PreferenceObservation(**dumped)
    assert loaded.category == "Shell"
    assert loaded.value == "PowerShell"
    assert loaded.timestamp.tzinfo == timezone.utc

def test_candidate_extraction():
    learner = PreferenceLearner(stabilization_threshold=0.6)
    
    base_time = datetime(2026, 7, 26, 10, 0, 0, tzinfo=timezone.utc)
    obs_list = [
        PreferenceObservation(user_id=1, category="Shell", value="PowerShell", timestamp=base_time, execution_status="SUCCESS"),
        PreferenceObservation(user_id=1, category="Shell", value="PowerShell", timestamp=base_time + timedelta(minutes=5), execution_status="SUCCESS"),
        PreferenceObservation(user_id=1, category="Shell", value="Bash", timestamp=base_time + timedelta(minutes=10), execution_status="SUCCESS"),
        PreferenceObservation(user_id=1, category="Browser", value="Chrome", timestamp=base_time, execution_status="SUCCESS", is_override=True),
    ]

    candidates = learner.extract_candidates(obs_list)
    assert len(candidates) == 3

    # Check PowerShell candidate
    pwsh_cand = next(c for c in candidates if c.value == "PowerShell")
    assert pwsh_cand.category == "Shell"
    assert pwsh_cand.observation_count == 2
    assert pwsh_cand.success_count == 2
    assert pwsh_cand.first_observed == base_time
    assert pwsh_cand.last_observed == base_time + timedelta(minutes=5)
    assert pwsh_cand.is_explicit is False

    # Check Chrome candidate
    chrome_cand = next(c for c in candidates if c.value == "Chrome")
    assert chrome_cand.category == "Browser"
    assert chrome_cand.observation_count == 1
    assert chrome_cand.is_explicit is True

def test_preference_scorer_calculations():
    # Custom scorer config
    scorer = PreferenceScorer(
        w_frequency=0.2,
        w_recency=0.4,
        w_success=0.2,
        w_override=0.2,
        half_life_seconds=3600.0,  # 1 hour half-life
        saturation_count=5
    )

    base_time = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    
    # Candidate with 1 observation, fresh (recency delta = 0), successful, no override
    cand = PreferenceCandidate(
        user_id=1,
        category="Shell",
        value="PowerShell",
        observation_count=1,
        success_count=1,
        first_observed=base_time,
        last_observed=base_time,
        is_explicit=False
    )
    
    obs = [
        PreferenceObservation(user_id=1, category="Shell", value="PowerShell", timestamp=base_time, execution_status="SUCCESS")
    ]

    score = scorer.compute_score(cand, obs, current_time=base_time)
    
    # S_freq = 1/5 = 0.2
    # S_rec = e^(0) = 1.0
    # S_succ = 1.0
    # S_over = 0.0
    # Score = 0.2*0.2 + 0.4*1.0 + 0.2*1.0 + 0.2*0.0 = 0.04 + 0.40 + 0.20 + 0.00 = 0.64
    assert pytest.approx(score, 0.0001) == 0.64

def test_exponential_decay():
    scorer = PreferenceScorer(
        w_frequency=0.0,
        w_recency=1.0,  # Only score recency
        w_success=0.0,
        w_override=0.0,
        half_life_seconds=3600.0  # 1 hour
    )

    base_time = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    
    cand = PreferenceCandidate(
        user_id=1, category="Shell", value="PowerShell",
        observation_count=1, success_count=1,
        first_observed=base_time, last_observed=base_time,
        is_explicit=False
    )
    obs = [
        PreferenceObservation(user_id=1, category="Shell", value="PowerShell", timestamp=base_time)
    ]

    # At t = base_time + 1 hour (exactly 1 half life)
    score = scorer.compute_score(cand, obs, current_time=base_time + timedelta(hours=1))
    assert pytest.approx(score, 0.001) == 0.5

    # At t = base_time + 2 hours (exactly 2 half lives)
    score_2 = scorer.compute_score(cand, obs, current_time=base_time + timedelta(hours=2))
    assert pytest.approx(score_2, 0.001) == 0.25

def test_override_priority():
    scorer = PreferenceScorer(
        w_frequency=0.1,
        w_recency=0.1,
        w_success=0.1,
        w_override=0.7,  # Override dominates
        half_life_seconds=86400.0,
        saturation_count=5
    )

    base_time = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    
    cand_no_override = PreferenceCandidate(
        user_id=1, category="Shell", value="PowerShell",
        observation_count=1, success_count=1,
        first_observed=base_time, last_observed=base_time,
        is_explicit=False
    )
    obs_no_override = [
        PreferenceObservation(user_id=1, category="Shell", value="PowerShell", timestamp=base_time, is_override=False)
    ]

    cand_override = PreferenceCandidate(
        user_id=1, category="Shell", value="Bash",
        observation_count=1, success_count=1,
        first_observed=base_time, last_observed=base_time,
        is_explicit=True
    )
    obs_override = [
        PreferenceObservation(user_id=1, category="Shell", value="Bash", timestamp=base_time, is_override=True)
    ]

    score_normal = scorer.compute_score(cand_no_override, obs_no_override, current_time=base_time)
    score_override = scorer.compute_score(cand_override, obs_override, current_time=base_time)

    # Override should be significantly higher
    assert score_override > score_normal
    assert score_override >= 0.7  # w_override * 1.0 is at least 0.7

def test_stability_threshold():
    learner = PreferenceLearner(stabilization_threshold=0.8)
    scorer = PreferenceScorer(w_frequency=1.0, w_recency=0.0, w_success=0.0, w_override=0.0, saturation_count=10)

    base_time = datetime.now(timezone.utc)
    
    # 5 observations -> freq score = 5/10 = 0.5. Stable? False (0.5 < 0.8)
    cand_unstable = PreferenceCandidate(
        user_id=1, category="Shell", value="PowerShell",
        observation_count=5, success_count=5,
        first_observed=base_time, last_observed=base_time
    )
    obs_unstable = [PreferenceObservation(user_id=1, category="Shell", value="PowerShell", timestamp=base_time) for _ in range(5)]
    assert learner.evaluate_stability(cand_unstable, scorer, obs_unstable) is False

    # 9 observations -> freq score = 9/10 = 0.9. Stable? True (0.9 >= 0.8)
    cand_stable = PreferenceCandidate(
        user_id=1, category="Shell", value="PowerShell",
        observation_count=9, success_count=9,
        first_observed=base_time, last_observed=base_time
    )
    obs_stable = [PreferenceObservation(user_id=1, category="Shell", value="PowerShell", timestamp=base_time) for _ in range(9)]
    assert learner.evaluate_stability(cand_stable, scorer, obs_stable) is True

def test_conflict_resolution():
    resolver = PreferenceConflictResolver()
    
    time_old = datetime(2026, 7, 26, 10, 0, 0, tzinfo=timezone.utc)
    time_new = datetime(2026, 7, 26, 11, 0, 0, tzinfo=timezone.utc)

    # 1. Conflict resolved by score
    p1 = ResolvedPreference(user_id=1, category="Shell", value="PowerShell", confidence_score=0.8, resolved_at=time_old, source="learned_stable")
    p2 = ResolvedPreference(user_id=1, category="Shell", value="Bash", confidence_score=0.9, resolved_at=time_old, source="learned_stable")
    assert resolver.resolve_conflict([p1, p2]).value == "Bash"

    # 2. Conflict resolved by override source (even if confidence_score is same)
    p3 = ResolvedPreference(user_id=1, category="Shell", value="PowerShell", confidence_score=0.8, resolved_at=time_old, source="explicit_override")
    p4 = ResolvedPreference(user_id=1, category="Shell", value="Bash", confidence_score=0.8, resolved_at=time_old, source="learned_stable")
    assert resolver.resolve_conflict([p3, p4]).value == "PowerShell"

    # 3. Conflict resolved by timestamp (newest first)
    p5 = ResolvedPreference(user_id=1, category="Shell", value="PowerShell", confidence_score=0.8, resolved_at=time_old, source="learned_stable")
    p6 = ResolvedPreference(user_id=1, category="Shell", value="Bash", confidence_score=0.8, resolved_at=time_new, source="learned_stable")
    assert resolver.resolve_conflict([p5, p6]).value == "Bash"

    # 4. Deterministic tie-breaker (alphabetical sorting of value string)
    p7 = ResolvedPreference(user_id=1, category="Shell", value="PowerShell", confidence_score=0.8, resolved_at=time_old, source="learned_stable")
    p8 = ResolvedPreference(user_id=1, category="Shell", value="Bash", confidence_score=0.8, resolved_at=time_old, source="learned_stable")
    assert resolver.resolve_conflict([p7, p8]).value == "Bash"  # "Bash" < "PowerShell"

@pytest.mark.anyio
async def test_coordinator_orchestration():
    # Setup mocks
    memory_service = AsyncMock()
    
    # Setup mock learner, scorer, conflict_resolver
    learner = PreferenceLearner(stabilization_threshold=0.5)
    scorer = PreferenceScorer(saturation_count=2, w_frequency=1.0, w_recency=0.0, w_success=0.0, w_override=0.0)
    conflict_resolver = PreferenceConflictResolver()

    coordinator = PreferenceLearningCoordinator(
        learner=learner,
        scorer=scorer,
        conflict_resolver=conflict_resolver,
        memory_service=memory_service
    )

    base_time = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)

    # Mock memory_service.get to return a completed execution activity
    exec_entry = MemoryEntry(
        id="exec_123_activity",
        content="Execution completed for shell PowerShell",
        memory_type=MemoryType.ACTIVITY,
        metadata=MemoryMetadata(
            created_at=base_time,
            additional_info={
                "status": "COMPLETED",
                "input_parameters": {"shell": "powershell"}
            }
        )
    )
    memory_service.get.return_value = exec_entry

    # Mock successful executions list containing another similar run
    other_entry = MemoryEntry(
        id="exec_124_activity",
        content="Execution completed",
        memory_type=MemoryType.ACTIVITY,
        metadata=MemoryMetadata(
            created_at=base_time - timedelta(minutes=10),
            additional_info={
                "status": "COMPLETED",
                "input_parameters": {"shell": "powershell"}
            }
        )
    )
    memory_service.get_successful_executions.return_value = [exec_entry, other_entry]
    
    # Mock no existing preferences
    memory_service.get_preference_by_key.return_value = None

    # Run coordinator process
    await coordinator.process_new_execution(user_id=99, execution_id="exec_123")

    # Assertions
    # memory_service.save should be called to persist the resolved Shell -> PowerShell preference
    memory_service.save.assert_called_once()
    saved_entry = memory_service.save.call_args[0][0]
    assert saved_entry.id == "Shell"
    assert saved_entry.content == "PowerShell"
    assert saved_entry.memory_type == MemoryType.PREFERENCE
    assert saved_entry.metadata.additional_info["user_id"] == 99
    assert saved_entry.metadata.additional_info["value"] == "PowerShell"
    assert saved_entry.metadata.additional_info["confidence_score"] == 1.0  # 2 obs / 2 saturation_count = 1.0

@pytest.mark.anyio
async def test_coordinator_manual_override():
    memory_service = AsyncMock()
    coordinator = PreferenceLearningCoordinator(
        learner=PreferenceLearner(),
        scorer=PreferenceScorer(),
        conflict_resolver=PreferenceConflictResolver(),
        memory_service=memory_service
    )

    resolved = await coordinator.register_manual_override(user_id=99, category="IDE", value="VS Code")

    assert resolved.user_id == 99
    assert resolved.category == "IDE"
    assert resolved.value == "VS Code"
    assert resolved.confidence_score == 1.0
    assert resolved.source == "explicit_override"

    memory_service.save.assert_called_once()
    saved_entry = memory_service.save.call_args[0][0]
    assert saved_entry.id == "IDE"
    assert saved_entry.content == "VS Code"
    assert saved_entry.metadata.additional_info["source"] == "explicit_override"
