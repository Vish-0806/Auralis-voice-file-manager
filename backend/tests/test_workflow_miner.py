# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from memory.workflows import (
    WorkflowMiningConfig,
    WorkflowPattern,
    WorkflowCandidate,
    MiningStatistics,
    WorkflowMiner,
)


def test_workflow_mining_config_defaults():
    config = WorkflowMiningConfig()
    assert config.min_support == 3
    assert config.min_confidence == 0.6
    assert config.max_sequence_length == 10
    assert config.min_sequence_length == 2


def test_workflow_mining_config_validation():
    # Test valid configuration
    config = WorkflowMiningConfig(min_support=1, min_confidence=0.0)
    assert config.min_support == 1

    # Test invalid configuration support under 1
    with pytest.raises(ValidationError):
        WorkflowMiningConfig(min_support=0)

    # Test invalid confidence limits
    with pytest.raises(ValidationError):
        WorkflowMiningConfig(min_confidence=1.1)

    with pytest.raises(ValidationError):
        WorkflowMiningConfig(min_confidence=-0.1)


def test_workflow_pattern_validation():
    # Valid pattern
    pat = WorkflowPattern(
        sequence_hash="abc",
        intents=["A", "B"],
        frequency=5,
        success_rate=0.8,
        average_duration_ms=120.0
    )
    assert pat.sequence_hash == "abc"
    assert pat.intents == ["A", "B"]

    # Invalid frequency under 0
    with pytest.raises(ValidationError):
        WorkflowPattern(sequence_hash="abc", frequency=-1)

    # Invalid success rate limits
    with pytest.raises(ValidationError):
        WorkflowPattern(sequence_hash="abc", success_rate=1.5)


def test_workflow_candidate_validation():
    # Valid candidate
    cand = WorkflowCandidate(
        sequence_hash="hash_x",
        steps=[{"intent": "CLICK"}],
        support_count=3,
        confidence=0.75
    )
    assert cand.sequence_hash == "hash_x"
    assert len(cand.steps) == 1

    # Invalid confidence limits
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

    # Naive timestamp string coercion test
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
    
    # Verify statistics when no run has occurred
    initial_stats = miner.statistics()
    assert initial_stats.sequences_analyzed == 0
    assert initial_stats.candidates_identified == 0
    assert initial_stats.patterns_mined == 0
    
    # Verify placeholder method returns
    assert miner.find_patterns([]) == []
    assert miner.build_candidates([]) == []
    
    # Run mine on empty list
    patterns = miner.mine([])
    assert patterns == []
    
    # Verify post-run statistics
    post_stats = miner.statistics()
    assert post_stats.sequences_analyzed == 0
    assert post_stats.candidates_identified == 0
    assert post_stats.patterns_mined == 0
    assert post_stats.run_duration_ms >= 0.0
