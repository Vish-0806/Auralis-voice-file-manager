"""Unit and integration tests for the Auralis Conversational Intelligence Engine."""

# pyrefly: ignore [missing-import]
import pytest
import os
import shutil
from datetime import datetime, timezone
from unittest.mock import MagicMock

from memory import MemoryService
from memory.models.domain_models import MemoryEntry, MemoryType, MemoryMetadata
from brain.conversation_intelligence.models import (
    DialogueState,
    DialoguePhase,
    PendingClarification,
    DialogueTurn,
    DialogueHistory,
)
from brain.conversation_intelligence.state_manager import DialogueStateManager
from brain.conversation_intelligence.followup_resolver import FollowUpResolver
from brain.conversation_intelligence.ambiguity_resolver import AmbiguityResolver
from brain.conversation_intelligence.clarification_manager import ClarificationManager
from brain.conversation_intelligence.history_manager import DialogueHistoryManager
from brain.conversation_intelligence.recovery_engine import ContextRecoveryEngine
from brain.conversation_intelligence.entity_linking import EntityLinkingEngine
from brain.conversation_intelligence.persistence import DialoguePersistenceManager
from brain.conversation_intelligence.runtime import ConversationalIntelligenceEngine
from brain.controller.models import BrainResponse, BrainStatus


# --- Unit Tests ---

def test_dialogue_state_management() -> None:
    """Verifies that dialogue state transitions and variables are updated correctly."""
    mgr = DialogueStateManager()
    state = mgr.get_state("session_1")
    assert state.session_id == "session_1"
    assert state.phase == DialoguePhase.IDLE

    mgr.transition_phase("session_1", DialoguePhase.WAITING_FOR_CLARIFICATION)
    state = mgr.get_state("session_1")
    assert state.phase == DialoguePhase.WAITING_FOR_CLARIFICATION

    mgr.set_active_task("session_1", "index_files")
    state = mgr.get_state("session_1")
    assert state.active_task == "index_files"
    assert state.phase == DialoguePhase.PROCESSING_TASK

    mgr.set_active_workflow("session_1", "deploy_workflow")
    state = mgr.get_state("session_1")
    assert state.active_workflow == "deploy_workflow"

    mgr.set_workspace("session_1", "C:/Projects/App")
    state = mgr.get_state("session_1")
    assert state.current_workspace == "C:/Projects/App"


def test_followup_resolver() -> None:
    """Verifies follow-up command resolution for relative commands."""
    linker = EntityLinkingEngine()
    resolver = FollowUpResolver(linker)

    assert resolver.is_followup("open it") is True
    assert resolver.is_followup("run again") is True
    assert resolver.is_followup("same folder") is True
    assert resolver.is_followup("delete this") is True
    assert resolver.is_followup("create files") is False

    state = DialogueState(session_id="session_1", current_workspace="C:/Projects/App")
    history = DialogueHistory(session_id="session_1")

    # Add a previous turn
    history.turns.append(DialogueTurn(
        turn_id="turn_1",
        role="user",
        content="open index.html",
        resolved_objects={"file": "index.html"}
    ))

    # Resolve "run again"
    res_cmd, _, _, _ = resolver.resolve("run again", state, history)
    assert res_cmd == "open index.html"

    # Resolve "same project"
    res_cmd, _, _, _ = resolver.resolve("open in same project", state, history)
    assert "C:/Projects/App" in res_cmd

    # Resolve pronoun
    linker.register_entity(state, "file", "index.html")
    res_cmd, _, _, _ = resolver.resolve("delete it", state, history)
    assert "index.html" in res_cmd


def test_clarification_manager() -> None:
    """Verifies that user answers are parsed and mapped to options."""
    mgr = ClarificationManager()
    pending = PendingClarification(
        clarification_id="clar_1",
        parameter_name="file",
        original_value="notes",
        options=["C:/Proj/A/notes.txt", "C:/Proj/B/notes.txt", "C:/Proj/C/notes.txt"],
        prompt="Which notes file?",
        command_to_resume="delete notes",
    )

    # Ordinals
    val, _ = mgr.resolve_clarification("the first one", pending)
    assert val == "C:/Proj/A/notes.txt"

    val, _ = mgr.resolve_clarification("second", pending)
    assert val == "C:/Proj/B/notes.txt"

    val, _ = mgr.resolve_clarification("3", pending)
    assert val == "C:/Proj/C/notes.txt"

    # String matching
    val, _ = mgr.resolve_clarification("Proj/B", pending)
    assert val == "C:/Proj/B/notes.txt"

    # Cancellation
    val, cancelled = mgr.resolve_clarification("cancel", pending)
    assert cancelled is True


def test_history_manager_and_branches() -> None:
    """Verifies turn logging, entities register, and sub-conversation branching."""
    mgr = DialogueHistoryManager()
    
    # Add main turns
    mgr.add_turn("session_1", "user", "run setup")
    mgr.add_turn("session_1", "assistant", "Starting setup. Which environment?")

    history = mgr.get_history("session_1")
    assert len(history.turns) == 2

    # Branching turn
    mgr.add_turn("session_1", "user", "what time is it?", branch_id="side_quest")
    mgr.add_turn("session_1", "assistant", "It is 12 PM.", branch_id="side_quest")

    assert len(history.turns) == 2
    assert len(history.branches["side_quest"]) == 2


def test_recovery_engine() -> None:
    """Verifies that dialogue context can be saved to snapshot and recovered."""
    state_mgr = DialogueStateManager()
    engine = ContextRecoveryEngine(state_mgr)

    state_mgr.set_workspace("session_1", "C:/Projects/MyProj")
    state_mgr.set_active_workflow("session_1", "MyWorkflow")

    # Save recovery snapshot
    engine.save_recovery_snapshot(
        "session_1",
        active_workflow="MyWorkflow",
        pending_execution={"command": "build project"},
    )

    # Reset in-memory state values
    state_mgr.set_workspace("session_1", None)
    state_mgr.set_active_workflow("session_1", None)

    # Recover
    snapshot = engine.recover_session("session_1")
    assert snapshot is not None
    assert snapshot["active_workflow"] == "MyWorkflow"
    assert snapshot["pending_execution"] == {"command": "build project"}

    state = state_mgr.get_state("session_1")
    assert state.current_workspace == "C:/Projects/MyProj"
    assert state.active_workflow == "MyWorkflow"


def test_entity_linking() -> None:
    """Verifies entity linking and reference resolution across turns."""
    engine = EntityLinkingEngine()
    state = DialogueState(session_id="session_1")
    history = DialogueHistory(session_id="session_1")

    # Link folder and file
    engine.register_entity(state, "folder", "C:/Downloads")
    engine.register_entity(state, "file", "invoice.pdf")

    # Verify retrieval
    assert engine.get_last_referenced("folder", state, history) == "C:/Downloads"
    assert engine.get_last_referenced("file", state, history) == "invoice.pdf"

    # Pronoun resolution should select the most recent one (file here)
    val, etype = engine.resolve_pronoun(state, history)
    assert val == "invoice.pdf"
    assert etype == "file"


# --- Integration & Ambiguity Tests ---

def test_ambiguity_resolver_workflows() -> None:
    """Verifies that ambiguous workflow names return a clarification request."""
    # Register dynamic workflow
    from automation.workflow.workflow_registry import WorkflowRegistry
    from automation.workflow.models import WorkflowDefinition
    WorkflowRegistry._dynamic_registry["Custom Study Mode"] = WorkflowDefinition(
        name="Custom Study Mode",
        description="Focused learning",
        steps=[]
    )

    try:
        resolver = AmbiguityResolver()
        state = DialogueState(session_id="session_1")

        # Let's say user command references "Study"
        pending = resolver.resolve_ambiguity("run Study", {}, state)
        assert pending is not None
        assert pending.parameter_name == "workflow"
        assert "Study Mode" in pending.options
        assert "Custom Study Mode" in pending.options
    finally:
        WorkflowRegistry._dynamic_registry.pop("Custom Study Mode", None)


def test_ambiguity_resolver_files(tmp_path) -> None:
    """Verifies that duplicate file names in workspace trigger clarification."""
    # Set up temp workspace with duplicate files
    proj_dir = tmp_path / "Project"
    proj_dir.mkdir()
    
    sub1 = proj_dir / "folderA"
    sub1.mkdir()
    sub2 = proj_dir / "folderB"
    sub2.mkdir()

    file1 = sub1 / "script.py"
    file1.write_text("print('A')")
    file2 = sub2 / "script.py"
    file2.write_text("print('B')")

    state = DialogueState(session_id="session_1", current_workspace=str(proj_dir))
    resolver = AmbiguityResolver()

    pending = resolver.resolve_ambiguity("run script.py", {}, state)
    assert pending is not None
    assert pending.parameter_name == "file"
    assert len(pending.options) == 2
    assert str(file1) in pending.options
    assert str(file2) in pending.options
    assert "I found multiple files matching" in pending.prompt


def test_conversational_engine_runtime_flow() -> None:
    """Simulates a multi-turn turn flow through the ConversationalIntelligenceEngine."""
    memory_service = MagicMock(spec=MemoryService)
    
    # Mock memory service methods
    async def dummy_save(entry): return entry
    async def dummy_get(id): return None
    memory_service.save.side_effect = dummy_save
    memory_service.get.side_effect = dummy_get

    engine = ConversationalIntelligenceEngine(memory_service)

    # Mock dispatcher and brain pipeline
    dispatcher = MagicMock()
    brain_pipeline = MagicMock()
    brain_pipeline.execute.return_value = BrainResponse(success=True, message="Done", goal_name="TEST")

    # Turn 1: Normal execution
    res = engine.process_turn("create document.txt", "sess_e2e", 1, None, dispatcher, brain_pipeline)
    assert res.success is True
    assert res.message == "Done"

    # Check entities linked
    state = engine.state_manager.get_state("sess_e2e")
    assert state.metadata["entities"]["file"]["value"] == "document.txt"

    # Turn 2: Relative command follow-up
    res_fu = engine.process_turn("open it", "sess_e2e", 1, None, dispatcher, brain_pipeline)
    assert res_fu.success is True
    brain_pipeline.execute.assert_called_with("open document.txt", dispatcher, context=None)
