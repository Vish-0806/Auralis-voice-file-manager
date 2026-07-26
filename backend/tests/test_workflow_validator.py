# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from core.intents import Intent
from memory.workflows import (
    WorkflowCandidate,
    WorkflowValidator,
    WorkflowMiner,
)
from automation.workflow.models import WorkflowDefinition
from automation.workflow.workflow_registry import WorkflowRegistry
from brain.planning.workflow_library import WorkflowLibrary


def test_successful_validation_and_promotion():
    # Valid candidate with valid intents and parameters
    cand = WorkflowCandidate(
        sequence_hash="hash_val",
        steps=[
            {"intent": "OPEN_APPLICATION", "target": "VS Code", "parameters": {}},
            {"intent": "SET_VOLUME", "target": "30", "parameters": {}}
        ],
        support_count=5,
        confidence=0.85,
        frequency=5,
        candidate_id="wf_123"
    )
    
    validator = WorkflowValidator(min_support=3, min_confidence=0.6)
    res = validator.validate_candidate(cand)
    assert res.is_valid is True
    assert len(res.issues) == 0

    miner = WorkflowMiner(validator=validator)
    definition = miner.promote_candidate(cand)
    
    assert isinstance(definition, WorkflowDefinition)
    assert definition.name == "Mined Workflow wf_123"
    assert len(definition.steps) == 2
    assert definition.steps[0].intent == Intent.OPEN_APPLICATION
    assert definition.steps[1].intent == Intent.SET_VOLUME
    
    # Verify compatibility with WorkflowRegistry
    registry = WorkflowRegistry()
    registry.register_workflow(definition)
    assert registry.get_workflow("Mined Workflow wf_123") == definition
    
    # Verify compatibility with WorkflowLibrary
    library = WorkflowLibrary(registry=registry)
    library.register_workflow(definition)
    assert library.get_workflow("Mined Workflow wf_123") == definition


def test_validation_support_and_confidence_failures():
    # Candidate with low support
    cand_low_support = WorkflowCandidate(
        sequence_hash="hash_val",
        steps=[{"intent": "MUTE", "parameters": {}}],
        support_count=2,  # Config demands 3
        confidence=0.8,
        frequency=2,
        candidate_id="wf_1"
    )
    
    validator = WorkflowValidator(min_support=3, min_confidence=0.6)
    res = validator.validate_candidate(cand_low_support)
    assert res.is_valid is False
    assert any(i.issue_type == "INSUFFICIENT_SUPPORT" for i in res.issues)

    # Candidate with low confidence
    cand_low_confidence = WorkflowCandidate(
        sequence_hash="hash_val",
        steps=[{"intent": "MUTE", "parameters": {}}],
        support_count=5,
        confidence=0.4,  # Config demands 0.6
        frequency=5,
        candidate_id="wf_2"
    )
    res = validator.validate_candidate(cand_low_confidence)
    assert res.is_valid is False
    assert any(i.issue_type == "INSUFFICIENT_CONFIDENCE" for i in res.issues)


def test_circular_dependency_detection():
    # Sequence of steps with circular intent loop: OPEN_APPLICATION -> SET_VOLUME -> OPEN_APPLICATION
    cand = WorkflowCandidate(
        sequence_hash="hash_val",
        steps=[
            {"intent": "OPEN_APPLICATION", "target": "VS Code", "parameters": {}},
            {"intent": "SET_VOLUME", "target": "30", "parameters": {}},
            {"intent": "OPEN_APPLICATION", "target": "Chrome", "parameters": {}}
        ],
        support_count=5,
        confidence=0.9,
        frequency=5,
        candidate_id="wf_3"
    )
    
    validator = WorkflowValidator(min_support=3, min_confidence=0.6)
    res = validator.validate_candidate(cand)
    # Circular dependency is a warning, so it is still valid
    assert res.is_valid is True
    assert any(i.issue_type == "CIRCULAR_DEPENDENCY" for i in res.issues)


def test_parameter_consistency_and_invalid_steps():
    # Step has an invalid parameters format (list instead of dict)
    cand_bad_params = WorkflowCandidate(
        sequence_hash="hash_val",
        steps=[
            {"intent": "MUTE", "parameters": []}  # Expected dict
        ],
        support_count=5,
        confidence=0.9,
        frequency=5,
        candidate_id="wf_4"
    )
    
    validator = WorkflowValidator()
    res = validator.validate_candidate(cand_bad_params)
    assert res.is_valid is False
    assert any(i.issue_type == "INVALID_PARAMETERS" for i in res.issues)

    # Step has an unknown/invalid step intent
    cand_bad_step = WorkflowCandidate(
        sequence_hash="hash_val",
        steps=[
            {"intent": "INVALID_ACTION_INTENT_NAME", "parameters": {}}
        ],
        support_count=5,
        confidence=0.9,
        frequency=5,
        candidate_id="wf_5"
    )
    res = validator.validate_candidate(cand_bad_step)
    assert res.is_valid is False
    assert any(i.issue_type == "INVALID_STEP" for i in res.issues)


def test_duplicate_workflow_detection():
    # Register name first
    validator = WorkflowValidator(
        min_support=1,
        min_confidence=0.1,
        existing_workflow_names=["Mined Workflow wf_dup"]
    )
    
    cand = WorkflowCandidate(
        sequence_hash="hash_val",
        steps=[{"intent": "MUTE", "parameters": {}}],
        support_count=5,
        confidence=0.9,
        frequency=5,
        candidate_id="wf_dup"
    )
    
    res = validator.validate_candidate(cand)
    assert res.is_valid is True  # Duplicate warning is non-blocking (warning)
    assert any(i.issue_type == "DUPLICATE_WORKFLOW" for i in res.issues)
