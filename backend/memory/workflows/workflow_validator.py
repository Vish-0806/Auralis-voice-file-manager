"""Validator class and schemas for verifying mined workflow candidates before promotion."""

import logging
from typing import Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from core.intents import Intent

logger = logging.getLogger(__name__)


class WorkflowValidationIssue(BaseModel):
    """Represents a specific validation issue identified in a workflow candidate."""

    issue_type: str = Field(..., description="Category identifier of the validation issue.")
    message: str = Field(..., description="User-facing detail description of the issue.")
    severity: str = Field(
        default="WARNING",
        description="Severity level of the validation issue (e.g., WARNING, ERROR)."
    )
    step_index: Optional[int] = Field(
        default=None,
        description="Zero-indexed position of the sequence step associated with this issue."
    )


class WorkflowValidationResult(BaseModel):
    """Result payload representing the outcome of a candidate validation pass."""

    is_valid: bool = Field(..., description="True if no ERROR severity issues were encountered.")
    issues: list[WorkflowValidationIssue] = Field(
        default_factory=list,
        description="Ordered list of validation issues found in the candidate."
    )


class WorkflowValidator:
    """Validator class for verifying workflow candidates before promotion."""

    def __init__(
        self,
        min_support: int = 3,
        min_confidence: float = 0.6,
        existing_workflow_names: Optional[list[str]] = None
    ) -> None:
        """Initializes the validator with support, confidence thresholds, and existing names."""
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.existing_workflow_names = existing_workflow_names or []

    def validate_candidate(self, candidate: Any) -> WorkflowValidationResult:
        """Validates a WorkflowCandidate against frequency, confidence, and sequence rules."""
        issues = []

        # 1. Validate minimum frequency / support threshold
        if candidate.support_count < self.min_support:
            issues.append(
                WorkflowValidationIssue(
                    issue_type="INSUFFICIENT_SUPPORT",
                    message=f"Candidate has support count {candidate.support_count}, expected at least {self.min_support}.",
                    severity="ERROR"
                )
            )

        # 2. Validate confidence threshold
        if candidate.confidence < self.min_confidence:
            issues.append(
                WorkflowValidationIssue(
                    issue_type="INSUFFICIENT_CONFIDENCE",
                    message=f"Candidate has confidence {candidate.confidence}, expected at least {self.min_confidence}.",
                    severity="ERROR"
                )
            )

        # 3. Validate duplicate workflows
        mined_name = f"Mined Workflow {candidate.candidate_id}"
        if mined_name in self.existing_workflow_names:
            issues.append(
                WorkflowValidationIssue(
                    issue_type="DUPLICATE_WORKFLOW",
                    message=f"Workflow with name '{mined_name}' already exists in registry/library.",
                    severity="WARNING"
                )
            )

        # 4. Circular dependencies (intents loop cycles)
        intents = [s.get("intent") for s in candidate.steps]
        seen_intents = {}
        for idx, intent in enumerate(intents):
            if intent in seen_intents:
                issues.append(
                    WorkflowValidationIssue(
                        issue_type="CIRCULAR_DEPENDENCY",
                        message=f"Circular action sequence detected: intent '{intent}' repeats at step {idx}.",
                        severity="WARNING",
                        step_index=idx
                    )
                )
            seen_intents[intent] = idx

        # 5. Invalid execution steps
        valid_intents = {item.value for item in Intent}
        for idx, s in enumerate(candidate.steps):
            intent_val = s.get("intent")
            if intent_val not in valid_intents:
                issues.append(
                    WorkflowValidationIssue(
                        issue_type="INVALID_STEP",
                        message=f"Step {idx} has invalid or unknown system intent '{intent_val}'.",
                        severity="ERROR",
                        step_index=idx
                    )
                )

        # 6. Parameter consistency
        for idx, s in enumerate(candidate.steps):
            params = s.get("parameters", {})
            if not isinstance(params, dict):
                issues.append(
                    WorkflowValidationIssue(
                        issue_type="INVALID_PARAMETERS",
                        message=f"Step {idx} has invalid parameters format. Expected dict, got {type(params).__name__}.",
                        severity="ERROR",
                        step_index=idx
                    )
                )

        is_valid = not any(issue.severity == "ERROR" for issue in issues)
        return WorkflowValidationResult(is_valid=is_valid, issues=issues)
