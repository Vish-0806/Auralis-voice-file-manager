# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
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


def create_sequence(intents: list[str], success: bool = True, duration_ms: float = 100.0) -> WorkflowSequence:
    steps = []
    t = datetime.now(timezone.utc)
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
        sequence_id="test-seq",
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
        confidence=0.75
    )
    assert cand.sequence_hash == "hash_x"
    assert len(cand.steps) == 1

    with pytest.raises(ValidationError):
        WorkflowCandidate(sequence_hash="abc", confidence=1.2)


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


def test_repeated_patterns_discovered():
    # Setup sequences sharing a repeated segment: ["A", "B", "C"]
    seq1 = create_sequence(["A", "B", "C", "D"])
    seq2 = create_sequence(["E", "A", "B", "C"])
    seq3 = create_sequence(["A", "B", "C"])
    
    # Require support of 3, confidence of 0.5
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=3, min_confidence=0.5, min_sequence_length=2))
    patterns = miner.mine([seq1, seq2, seq3])
    
    # We expect "A,B", "B,C", and "A,B,C" patterns to have support >= 3
    # Check that "A,B,C" is indeed mined
    pattern_intents = [p.intents for p in patterns]
    assert ["A", "B", "C"] in pattern_intents
    assert ["A", "B"] in pattern_intents
    assert ["B", "C"] in pattern_intents


def test_overlapping_patterns_handled():
    # Sequence with overlapping contiguous subsequences: ["A", "A", "A", "A"]
    # For pattern ["A", "A"], sliding window occurrences are 3: idx 0, 1, 2.
    seq = create_sequence(["A", "A", "A", "A"])
    
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=1, min_confidence=0.1, min_sequence_length=2))
    patterns = miner.mine([seq])
    
    # "A, A" should have frequency 3
    pattern_aa = next(p for p in patterns if p.intents == ["A", "A"])
    assert pattern_aa.frequency == 3


def test_insufficient_support_filtering():
    seq1 = create_sequence(["A", "B"])
    seq2 = create_sequence(["A", "B"])
    seq3 = create_sequence(["X", "Y"])
    
    # Require min_support = 3
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=3, min_confidence=0.5, min_sequence_length=2))
    patterns = miner.mine([seq1, seq2, seq3])
    
    # "A, B" support is 2, so it should not be mined
    assert len(patterns) == 0


def test_deterministic_ordering():
    # Setup candidate patterns:
    # Pattern 1: confidence=1.0, frequency=4, length=2
    # Pattern 2: confidence=1.0, frequency=4, length=3
    # Pattern 3: confidence=0.8, frequency=5, length=2
    
    seq1 = create_sequence(["A", "B", "C", "D"])
    seq2 = create_sequence(["A", "B", "C", "D"])
    seq3 = create_sequence(["A", "B", "C"])
    seq4 = create_sequence(["A", "B", "E"])
    
    # Under this layout:
    # "A,B" has frequency 4, support 4. Prefix "A" has frequency 4. Confidence = 4/4 = 1.0. length = 2.
    # "B,C" has frequency 3, support 3. Prefix "B" has frequency 4. Confidence = 3/4 = 0.75. length = 2.
    
    miner = WorkflowMiner(config=WorkflowMiningConfig(min_support=2, min_confidence=0.1, min_sequence_length=2))
    patterns = miner.mine([seq1, seq2, seq3, seq4])
    
    # Check that sorting orders highest confidence first
    for i in range(len(patterns) - 1):
        p1, p2 = patterns[i], patterns[i+1]
        if p1.confidence == p2.confidence:
            if p1.frequency == p2.frequency:
                assert len(p1.intents) >= len(p2.intents)
            else:
                assert p1.frequency >= p2.frequency
        else:
            assert p1.confidence >= p2.confidence
