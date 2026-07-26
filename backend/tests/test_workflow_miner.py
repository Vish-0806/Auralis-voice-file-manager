# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from memory.workflows import (
    WorkflowStepObservation,
    WorkflowSequence,
    WorkflowMiningConfig,
    WorkflowPattern,
    WorkflowCandidate,
    MiningStatistics,
    WorkflowMiner,
)


def create_sequence(intents: list[str], success: bool = True, duration_ms: float = 100.0, sequence_id: str = "seq-1", start_time: datetime = None) -> WorkflowSequence:
    steps = []
    t = start_time or datetime.now(timezone.utc)
    for i, intent in enumerate(intents):
        steps.append(
            WorkflowStepObservation(
                step_id=f"s_{i}",
                intent=intent,
                status="SUCCESS" if success else "FAILED",
                duration_ms=duration_ms,
                timestamp=t
            )
        )
    return WorkflowSequence(
        steps=steps,
        sequence_id=sequence_id,
        sequence_hash="test-hash",
        total_duration_ms=duration_ms * len(intents)
    )


def test_workflow_mining_config_defaults():
    config = WorkflowMiningConfig()
    assert config.min_support == 3
    assert config.min_confidence == 0.6
    assert config.max_sequence_length == 10
    assert config.min_sequence_length == 2


def test_workflow_mining_config_validation():
    config = WorkflowMiningConfig(min_support=1, min_confidence=0.0)
    assert config.min_support == 1

    with pytest.raises(ValidationError):
        WorkflowMiningConfig(min_support=0)

    with pytest.raises(ValidationError):
        WorkflowMiningConfig(min_confidence=1.1)

    with pytest.raises(ValidationError):
        WorkflowMiningConfig(min_confidence=-0.1)


def test_workflow_pattern_validation():
    pat = WorkflowPattern(
        sequence_hash="abc",
        intents=["A", "B"],
        frequency=5,
        confidence=0.9,
        success_rate=0.8,
        average_duration_ms=120.0
    )
    assert pat.sequence_hash == "abc"
    assert pat.intents == ["A", "B"]

    with pytest.raises(ValidationError):
        WorkflowPattern(sequence_hash="abc", frequency=-1)

    with pytest.raises(ValidationError):
        WorkflowPattern(sequence_hash="abc", success_rate=1.5)


def test_workflow_candidate_validation():
    cand = WorkflowCandidate(
        sequence_hash="hash_x",
        steps=[{"intent": "CLICK"}],
        support_count=3,
        confidence=0.75,
        candidate_id="wf_abc"
    )
    assert cand.sequence_hash == "hash_x"
    assert len(cand.steps) == 1

    with pytest.raises(ValidationError):
        WorkflowCandidate(sequence_hash="abc", confidence=1.2, candidate_id="wf_abc")


def test_mining_statistics_validation():
    now = datetime.now(timezone.utc)
    stats = MiningStatistics(
        sequences_analyzed=10,
        candidates_identified=5,
        patterns_mined=2,
        run_duration_ms=25.5,
        timestamp=now
    )
    assert stats.sequences_analyzed == 10
    assert stats.timestamp == now

    stats_naive = MiningStatistics(timestamp="2026-07-26T12:00:00")
    assert stats_naive.timestamp.tzinfo is not None
    assert stats_naive.timestamp.tzinfo == timezone.utc


def test_workflow_miner_constructor_injection():
    config = WorkflowMiningConfig(min_support=5, min_confidence=0.8)
    miner = WorkflowMiner(config=config)
    assert miner.config.min_support == 5
    assert miner.config.min_confidence == 0.8


def test_workflow_miner_empty_inputs_and_placeholders():
    miner = WorkflowMiner()
    
    initial_stats = miner.statistics()
    assert initial_stats.sequences_analyzed == 0
    assert initial_stats.candidates_identified == 0
    assert initial_stats.patterns_mined == 0
    
    assert miner.find_patterns([]) == []
    assert miner.build_candidates([]) == []
    
    patterns = miner.mine([])
    assert patterns == []
    
    post_stats = miner.statistics()
    assert post_stats.sequences_analyzed == 0
    assert post_stats.candidates_identified == 0
    assert post_stats.patterns_mined == 0
    assert post_stats.run_duration_ms >= 0.0


def test_candidate_construction_and_statistics():
    t1 = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 26, 12, 10, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 7, 26, 12, 30, 0, tzinfo=timezone.utc)
    
    # 3 occurrences of ["A", "B"]
    seq1 = create_sequence(["A", "B", "C"], sequence_id="s1", start_time=t1)
    seq2 = create_sequence(["A", "B", "D"], sequence_id="s2", start_time=t2)
    seq3 = create_sequence(["X", "A", "B"], sequence_id="s3", start_time=t3)
    
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=3, min_confidence=0.5, min_sequence_length=2))
    candidates = miner.build_candidates([seq1, seq2, seq3])
    
    # Find candidate for ["A", "B"]
    candidate_ab = next(c for c in candidates if [s["intent"] for s in c.steps] == ["A", "B"])
    
    assert candidate_ab.frequency == 3
    assert candidate_ab.support_count == 3
    assert candidate_ab.first_seen == t1
    assert candidate_ab.last_seen == t3
    assert set(candidate_ab.source_sequence_references) == {"s1", "s2", "s3"}
    assert candidate_ab.candidate_id.startswith("wf_")


def test_candidate_rejection_rules():
    seq1 = create_sequence(["A", "B"])
    seq2 = create_sequence(["A", "B"])
    seq3 = create_sequence(["A", "C"])
    
    # Require support of 3
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=3, min_confidence=0.5, min_sequence_length=2))
    candidates = miner.build_candidates([seq1, seq2, seq3])
    
    # Under support count 3, "A, B" (support 2) must be rejected
    assert len(candidates) == 0


def test_identifier_stability():
    seq1 = create_sequence(["A", "B"])
    seq2 = create_sequence(["A", "B"])
    seq3 = create_sequence(["A", "B"])
    
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=2, min_confidence=0.5, min_sequence_length=2))
    candidates1 = miner.build_candidates([seq1, seq2])
    candidates2 = miner.build_candidates([seq2, seq3])
    
    # Identifiers must be deterministic and identical
    c1 = next(c for c in candidates1 if [s["intent"] for s in c.steps] == ["A", "B"])
    c2 = next(c for c in candidates2 if [s["intent"] for s in c.steps] == ["A", "B"])
    
    assert c1.candidate_id == c2.candidate_id


def test_execution_interval_calculation():
    t1 = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 26, 12, 5, 0, tzinfo=timezone.utc)  # +300 seconds
    t3 = datetime(2026, 7, 26, 12, 15, 0, tzinfo=timezone.utc) # +600 seconds
    
    seq1 = create_sequence(["A", "B"], start_time=t1)
    seq2 = create_sequence(["A", "B"], start_time=t2)
    seq3 = create_sequence(["A", "B"], start_time=t3)
    
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=3, min_confidence=0.5, min_sequence_length=2))
    candidates = miner.build_candidates([seq1, seq2, seq3])
    
    c = next(c for c in candidates if [s["intent"] for s in c.steps] == ["A", "B"])
    
    # Intervals are 300s and 600s -> average interval should be 450s
    assert c.average_execution_interval == 450.0
