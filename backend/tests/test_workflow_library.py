"""Unit tests for the Workflow Library subsystem in Auralis."""

from __future__ import annotations

import pytest
from core.intents import Intent
from automation.workflow.models import WorkflowStep, WorkflowDefinition
from brain.planning.workflow_library import (
    WorkflowLibrary,
    WorkflowMetadata,
    WorkflowSignature,
    WorkflowTag,
)


def test_workflow_library_initialization_defaults():
    """Checks that the WorkflowLibrary prepopulates defaults properly."""
    lib = WorkflowLibrary()

    workflows = lib.list_workflows()
    assert len(workflows) >= 5

    names = [w.name for w in workflows]
    assert "Start Coding" in names
    assert "Study Mode" in names

    meta_coding = lib.get_metadata("Start Coding")
    assert meta_coding is not None
    assert meta_coding.goal_name == "START_CODING"
    assert "code" in meta_coding.tags
    assert "dev" in meta_coding.tags


def test_workflow_library_registration_and_lookup():
    """Checks dynamic registration, metadata binding, and deterministic queries."""
    lib = WorkflowLibrary()

    # Create dummy workflow definition
    wf = WorkflowDefinition(
        name="Custom Build Routine",
        description="Compiles backend code and runs validation",
        steps=[
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Terminal"),
            WorkflowStep(intent=Intent.ENABLE_WIFI),
        ],
    )

    meta = WorkflowMetadata(
        goal_name="RUN_BUILD",
        tags=["build", "CI", "compilation"],
        signature=WorkflowSignature(inputs=["env_name"], outputs=["build_success"]),
        author="TestAuthor",
    )

    # Register
    lib.register_workflow(wf, meta)

    # Get and check metadata
    meta_retrieved = lib.get_metadata("Custom Build Routine")
    assert meta_retrieved is not None
    assert meta_retrieved.author == "TestAuthor"
    assert "compilation" in meta_retrieved.tags
    assert meta_retrieved.signature.inputs == ["env_name"]

    # 1. Lookup by name
    assert len(lib.lookup_by_name("Custom Build Routine")) == 1
    assert len(lib.lookup_by_name("Non-existent")) == 0

    # 2. Lookup by goal
    assert len(lib.lookup_by_goal("RUN_BUILD")) == 1
    assert len(lib.lookup_by_goal("run_build")) == 1  # Case-insensitive

    # 3. Lookup by intent
    assert len(lib.lookup_by_intent(Intent.ENABLE_WIFI)) > 0
    # Custom Build Routine has OPEN_APPLICATION and ENABLE_WIFI
    matching_intents = lib.lookup_by_intent(Intent.ENABLE_WIFI)
    assert any(w.name == "Custom Build Routine" for w in matching_intents)

    # 4. Lookup by tags
    assert len(lib.lookup_by_tags(["CI", "build"])) == 1
    assert len(lib.lookup_by_tags(["CI", "non_matching"])) == 0


def test_workflow_library_deregistration():
    """Checks that workflows are correctly pruned upon deregistration."""
    lib = WorkflowLibrary()

    wf = WorkflowDefinition(
        name="Deregister Target",
        description="Target description",
        steps=[WorkflowStep(intent=Intent.MUTE)],
    )
    lib.register_workflow(wf, WorkflowMetadata(goal_name="DEREGISTER_TEST", tags=["temporary"]))

    assert len(lib.lookup_by_name("Deregister Target")) == 1
    assert lib.get_metadata("Deregister Target") is not None

    # Deregister
    lib.deregister_workflow("Deregister Target")

    assert len(lib.lookup_by_name("Deregister Target")) == 0
    assert lib.get_metadata("Deregister Target") is None


def test_workflow_tag_and_signature_instantiation():
    """Tests Pydantic validation for tags and signature helpers."""
    tag = WorkflowTag(name="production")
    sig = WorkflowSignature(inputs=["a", "b"], outputs=["result"])

    assert tag.name == "production"
    assert sig.inputs == ["a", "b"]
    assert sig.outputs == ["result"]
