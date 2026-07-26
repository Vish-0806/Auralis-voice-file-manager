"""Pydantic schemas and orchestration module for Auralis Workflow Mining."""

import hashlib
from datetime import datetime, timezone
from typing import Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator

from memory.workflows.workflow_models import WorkflowSequence, ensure_utc


class WorkflowMiningConfig(BaseModel):
    """Configuration settings for the workflow mining process."""

    min_support: int = Field(
        default=3,
        ge=1,
        description="Minimum frequency support count to consider a pattern."
    )
    min_confidence: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for mining rules."
    )
    max_sequence_length: int = Field(
        default=10,
        ge=1,
        description="Maximum step sequence length to mine."
    )
    min_sequence_length: int = Field(
        default=2,
        ge=1,
        description="Minimum step sequence length to mine."
    )


class WorkflowPattern(BaseModel):
    """Represents a validated, recurrent sequence pattern mined from history."""

    sequence_hash: str = Field(
        ...,
        description="Deterministic hash identifying this sequence pattern."
    )
    intents: list[str] = Field(
        default_factory=list,
        description="Ordered intent list describing the pattern steps."
    )
    frequency: int = Field(
        default=0,
        ge=0,
        description="Frequency count of pattern occurrence in the mined logs."
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Calculated confidence probability of this recurrent pattern."
    )
    success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Success rate rating of this mined pattern (0.0 to 1.0)."
    )
    average_duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Average execution duration in milliseconds."
    )


class WorkflowCandidate(BaseModel):
    """Represents a potential workflow pattern candidate during mining passes."""

    sequence_hash: str = Field(
        ...,
        description="Deterministic hash identifying this candidate sequence."
    )
    steps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Step properties stored in the candidate pattern."
    )
    support_count: int = Field(
        default=0,
        ge=0,
        description="Support observation count for this candidate pattern."
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Calculated confidence probability of this candidate pattern."
    )
    frequency: int = Field(
        default=0,
        ge=0,
        description="Frequency count of pattern occurrence in the logs."
    )
    average_execution_interval: float = Field(
        default=0.0,
        ge=0.0,
        description="Average execution interval in seconds between pattern occurrences."
    )
    first_seen: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the first occurrence of this pattern."
    )
    last_seen: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the last occurrence of this pattern."
    )
    source_sequence_references: list[str] = Field(
        default_factory=list,
        description="List of sequence IDs where this pattern was observed."
    )
    candidate_id: str = Field(
        ...,
        description="Stable, deterministically generated workflow identifier."
    )


class MiningStatistics(BaseModel):
    """Execution statistics summary for a single workflow mining invocation."""

    sequences_analyzed: int = Field(
        default=0,
        ge=0,
        description="Number of workflow sequences analyzed."
    )
    candidates_identified: int = Field(
        default=0,
        ge=0,
        description="Number of candidate patterns discovered."
    )
    patterns_mined: int = Field(
        default=0,
        ge=0,
        description="Number of recurrent patterns validated."
    )
    run_duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution duration of the mining algorithm in milliseconds."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware timestamp when statistics were computed."
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> Optional[datetime]:
        """Validates and enforces UTC timezone on timestamp."""
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        return ensure_utc(v)


class WorkflowMiner:
    """Orchestrates sequence pattern mining from recorded workflow runs."""

    def __init__(self, config: Optional[WorkflowMiningConfig] = None, validator: Optional[Any] = None) -> None:
        """Initializes the miner with configuration guidelines and optional validator."""
        self.config = config or WorkflowMiningConfig()
        from memory.workflows.workflow_validator import WorkflowValidator
        self.validator = validator or WorkflowValidator(
            min_support=self.config.min_support,
            min_confidence=self.config.min_confidence
        )
        self._last_stats: Optional[MiningStatistics] = None

    def mine(self, sequences: list[WorkflowSequence]) -> list[WorkflowPattern]:
        """Performs full end-to-end workflow pattern mining on input sequences."""
        start_time = datetime.now(timezone.utc)

        candidates = self.build_candidates(sequences)
        patterns = self.find_patterns(sequences)

        valid_patterns = []
        for pat in patterns:
            # Reconstruct candidate to validate it
            candidate_steps = [{"intent": intent} for intent in pat.intents]
            mock_cand = WorkflowCandidate(
                sequence_hash=pat.sequence_hash,
                steps=candidate_steps,
                support_count=pat.frequency,
                confidence=pat.confidence,
                frequency=pat.frequency,
                candidate_id=f"wf_{pat.sequence_hash[:12]}"
            )
            validation_res = self.validator.validate_candidate(mock_cand)
            if validation_res.is_valid:
                valid_patterns.append(pat)

        run_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0
        self._last_stats = MiningStatistics(
            sequences_analyzed=len(sequences),
            candidates_identified=len(candidates),
            patterns_mined=len(valid_patterns),
            run_duration_ms=run_time,
            timestamp=datetime.now(timezone.utc)
        )
        return valid_patterns

    def find_patterns(self, sequences: list[WorkflowSequence]) -> list[WorkflowPattern]:
        """Finds recurrent patterns filtering by support and confidence limits."""
        if not sequences:
            return []

        freq_map = {}
        support_map = {}
        duration_map = {}
        success_map = {}

        for seq_idx, sequence in enumerate(sequences):
            intents = [step.intent for step in sequence.steps]
            n = len(intents)
            seen_in_seq = set()
            for L in range(1, self.config.max_sequence_length + 1):
                for i in range(n - L + 1):
                    sub_seq = tuple(intents[i : i + L])
                    matched_steps = sequence.steps[i : i + L]

                    duration = sum(step.duration_ms for step in matched_steps)
                    success = all(step.status == "SUCCESS" for step in matched_steps)

                    freq_map[sub_seq] = freq_map.get(sub_seq, 0) + 1
                    duration_map[sub_seq] = duration_map.get(sub_seq, 0.0) + duration
                    if success:
                        success_map[sub_seq] = success_map.get(sub_seq, 0) + 1

                    if sub_seq not in seen_in_seq:
                        seen_in_seq.add(sub_seq)
                        if sub_seq not in support_map:
                            support_map[sub_seq] = set()
                        support_map[sub_seq].add(seq_idx)

        patterns = []
        for sub_seq, freq in freq_map.items():
            L = len(sub_seq)
            if self.config.min_sequence_length <= L <= self.config.max_sequence_length:
                support = len(support_map[sub_seq])
                if support < self.config.min_support:
                    continue

                if L == 1:
                    confidence = 1.0
                else:
                    prefix = sub_seq[:-1]
                    prefix_freq = freq_map.get(prefix, 0)
                    confidence = freq / prefix_freq if prefix_freq > 0 else 0.0

                if confidence < self.config.min_confidence:
                    continue

                avg_duration = duration_map[sub_seq] / freq if freq > 0 else 0.0
                success_rate = success_map.get(sub_seq, 0) / freq if freq > 0 else 0.0

                intents_str = ",".join(sub_seq)
                seq_hash = hashlib.sha256(intents_str.encode("utf-8")).hexdigest()

                patterns.append(
                    WorkflowPattern(
                        sequence_hash=seq_hash,
                        intents=list(sub_seq),
                        frequency=freq,
                        confidence=confidence,
                        success_rate=success_rate,
                        average_duration_ms=avg_duration
                    )
                )

        # Sort by confidence desc, frequency desc, sequence length desc, then sequence_hash asc
        patterns.sort(key=lambda p: (-p.confidence, -p.frequency, -len(p.intents), p.sequence_hash))
        return patterns

    def build_candidates(self, sequences: list[WorkflowSequence]) -> list[WorkflowCandidate]:
        """Builds potential candidate patterns from sequence occurrences."""
        if not sequences:
            return []

        freq_map = {}
        support_map = {}
        occurrence_times = {}
        seq_refs_map = {}

        for seq_idx, sequence in enumerate(sequences):
            intents = [step.intent for step in sequence.steps]
            n = len(intents)
            seen_in_seq = set()
            for L in range(1, self.config.max_sequence_length + 1):
                for i in range(n - L + 1):
                    sub_seq = tuple(intents[i : i + L])
                    freq_map[sub_seq] = freq_map.get(sub_seq, 0) + 1

                    if sub_seq not in occurrence_times:
                        occurrence_times[sub_seq] = []
                    occurrence_times[sub_seq].append(sequence.steps[i].timestamp)

                    if sub_seq not in seq_refs_map:
                        seq_refs_map[sub_seq] = set()
                    if sequence.sequence_id:
                        seq_refs_map[sub_seq].add(sequence.sequence_id)

                    if sub_seq not in seen_in_seq:
                        seen_in_seq.add(sub_seq)
                        if sub_seq not in support_map:
                            support_map[sub_seq] = set()
                        support_map[sub_seq].add(seq_idx)

        candidates = []
        for sub_seq, freq in freq_map.items():
            L = len(sub_seq)
            if self.config.min_sequence_length <= L <= self.config.max_sequence_length:
                support_count = len(support_map[sub_seq])

                if support_count < self.config.min_support:
                    continue

                if L == 1:
                    confidence = 1.0
                else:
                    prefix = sub_seq[:-1]
                    prefix_freq = freq_map.get(prefix, 0)
                    confidence = freq / prefix_freq if prefix_freq > 0 else 0.0

                if confidence < self.config.min_confidence:
                    continue

                times = sorted(occurrence_times[sub_seq])
                first_seen = times[0]
                last_seen = times[-1]

                if len(times) >= 2:
                    intervals = [(times[j+1] - times[j]).total_seconds() for j in range(len(times) - 1)]
                    avg_interval = sum(intervals) / len(intervals)
                else:
                    avg_interval = 0.0

                intents_str = ",".join(sub_seq)
                seq_hash = hashlib.sha256(intents_str.encode("utf-8")).hexdigest()
                candidate_id = f"wf_{seq_hash[:12]}"

                candidates.append(
                    WorkflowCandidate(
                        sequence_hash=seq_hash,
                        steps=[{"intent": intent} for intent in sub_seq],
                        support_count=support_count,
                        confidence=confidence,
                        frequency=freq,
                        average_execution_interval=avg_interval,
                        first_seen=first_seen,
                        last_seen=last_seen,
                        source_sequence_references=list(sorted(seq_refs_map[sub_seq])),
                        candidate_id=candidate_id
                    )
                )

        # Order candidates deterministically: confidence desc, support desc, length desc, candidate_id asc
        candidates.sort(key=lambda c: (-c.confidence, -c.support_count, -len(c.steps), c.candidate_id))
        return candidates

    def statistics(self) -> MiningStatistics:
        """Retrieves statistics from the most recent mining execution run."""
        if self._last_stats is None:
            return MiningStatistics(
                sequences_analyzed=0,
                candidates_identified=0,
                patterns_mined=0,
                run_duration_ms=0.0,
                timestamp=datetime.now(timezone.utc)
            )
        return self._last_stats

    def promote_candidate(self, candidate: WorkflowCandidate) -> Any:
        """Promotes a validated WorkflowCandidate to a WorkflowDefinition."""
        validation_res = self.validator.validate_candidate(candidate)
        if not validation_res.is_valid:
            errors = [i.message for i in validation_res.issues if i.severity == "ERROR"]
            raise ValueError(f"Cannot promote invalid candidate: {'; '.join(errors)}")

        from automation.workflow.models import WorkflowStep, WorkflowDefinition
        from core.intents import Intent

        steps = []
        for s in candidate.steps:
            intent_str = s.get("intent")
            try:
                intent_enum = Intent(intent_str)
            except ValueError:
                raise ValueError(f"Invalid intent '{intent_str}' during candidate promotion.")

            steps.append(
                WorkflowStep(
                    intent=intent_enum,
                    target=s.get("target"),
                    parameters=s.get("parameters", {})
                )
            )

        name = f"Mined Workflow {candidate.candidate_id}"
        description = (
            f"Mined workflow from logs. Support count: {candidate.support_count}, "
            f"confidence: {candidate.confidence:.2f}, frequency: {candidate.frequency}."
        )

        return WorkflowDefinition(
            name=name,
            description=description,
            steps=steps
        )
