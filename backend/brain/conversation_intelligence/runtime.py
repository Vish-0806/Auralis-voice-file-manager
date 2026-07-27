"""Main orchestrator for the Conversational Intelligence Engine."""

from __future__ import annotations

import logging
from typing import Any, Optional
import uuid

from memory import MemoryService
from brain.controller.models import BrainResponse
from brain.conversation_intelligence.models import DialogueState, DialoguePhase, PendingClarification, DialogueTurn
from brain.conversation_intelligence.persistence import DialoguePersistenceManager
from brain.conversation_intelligence.state_manager import DialogueStateManager
from brain.conversation_intelligence.history_manager import DialogueHistoryManager
from brain.conversation_intelligence.followup_resolver import FollowUpResolver
from brain.conversation_intelligence.ambiguity_resolver import AmbiguityResolver
from brain.conversation_intelligence.clarification_manager import ClarificationManager
from brain.conversation_intelligence.recovery_engine import ContextRecoveryEngine
from brain.conversation_intelligence.entity_linking import EntityLinkingEngine

logger = logging.getLogger(__name__)


class ConversationalIntelligenceEngine:
    """Orchestrates multi-turn conversation tracking, context resolution, and ambiguities."""

    def __init__(self, memory_service: MemoryService) -> None:
        self.persistence = DialoguePersistenceManager(memory_service)
        self.state_manager = DialogueStateManager(self.persistence)
        self.history_manager = DialogueHistoryManager(self.persistence)
        self.entity_linker = EntityLinkingEngine()
        self.followup_resolver = FollowUpResolver(self.entity_linker)
        self.ambiguity_resolver = AmbiguityResolver()
        self.clarification_manager = ClarificationManager()
        self.recovery_engine = ContextRecoveryEngine(self.state_manager)

    def process_turn(
        self,
        command: str,
        session_id: str,
        user_id: int,
        assistant_context: Optional[Any],
        dispatcher: Any,
        brain_pipeline: Any,
    ) -> BrainResponse:
        """Processes a single conversation turn through dialogue, resolver, and execution layers."""
        logger.info("Conversational intelligence engine processing turn for session %s", session_id)

        # 1. Retrieve dialogue state and history
        state = self.state_manager.get_state(session_id)
        history = self.history_manager.get_history(session_id)

        # Update workspace in state if available
        if assistant_context and assistant_context.workspace_context:
            state.current_workspace = assistant_context.workspace_context.content
            self.state_manager.save_state(state)

        # 2. Check if we are waiting for a clarification response
        if state.phase == DialoguePhase.WAITING_FOR_CLARIFICATION and state.pending_clarification:
            pending = state.pending_clarification
            resolved_val, is_cancelled = self.clarification_manager.resolve_clarification(command, pending)

            if is_cancelled:
                # User aborted the action
                self.state_manager.set_pending_clarification(session_id, None)
                self.history_manager.add_turn(session_id, "user", command)
                msg = "Action cancelled."
                self.history_manager.add_turn(session_id, "assistant", msg)
                return BrainResponse(
                    success=True,
                    message=msg,
                    goal_name="CANCEL",
                )

            if resolved_val:
                # Substitution: replace original ambiguous target with the resolved absolute path/option
                # Try simple substitution: replace parameter in command string
                orig_val = pending.original_value
                resolved_cmd = pending.command_to_resume.replace(orig_val, resolved_val)

                logger.info("Clarification resolved. Resuming command: '%s'", resolved_cmd)

                # Clear pending clarification and transition phase
                self.state_manager.set_pending_clarification(session_id, None)
                self.state_manager.transition_phase(session_id, DialoguePhase.PROCESSING_TASK)

                # Record user input in history
                self.history_manager.add_turn(
                    session_id,
                    "user",
                    command,
                    entities={pending.parameter_name: resolved_val},
                    resolved_objects={pending.parameter_name: resolved_val},
                )
                self.entity_linker.register_entity(state, pending.parameter_name, resolved_val)

                # Execute original command with resolved parameter
                response = brain_pipeline.execute(resolved_cmd, dispatcher, context=assistant_context)

                # Track workflow or routine if executed
                if response.success:
                    if pending.parameter_name == "workflow":
                        self.state_manager.set_active_workflow(session_id, resolved_val)
                    self.state_manager.transition_phase(session_id, DialoguePhase.COMPLETED)
                else:
                    self.state_manager.transition_phase(session_id, DialoguePhase.IDLE)

                # Record assistant turn in history
                self.history_manager.add_turn(session_id, "assistant", response.message)
                return response

            else:
                # Answer not resolved to any option, ask again
                self.history_manager.add_turn(session_id, "user", command)
                prompt = pending.prompt
                self.history_manager.add_turn(session_id, "assistant", prompt)
                return BrainResponse(
                    success=False,
                    message=prompt,
                    goal_name="CLARIFY",
                )

        # 3. Resolve relative command follow-ups (e.g. "open it", "run again")
        is_fu = self.followup_resolver.is_followup(command)
        resolved_entities = {}
        if is_fu:
            logger.info("Follow-up command detected: '%s'", command)
            resolved_cmd, resolved_entities, req_clar, clar_prompt = self.followup_resolver.resolve(
                command, state, history, assistant_context
            )
            if req_clar:
                # Prompt for clarification on unresolved follow-up
                self.history_manager.add_turn(session_id, "user", command)
                self.history_manager.add_turn(session_id, "assistant", clar_prompt)
                return BrainResponse(
                    success=False,
                    message=clar_prompt,
                    goal_name="CLARIFY",
                )
        else:
            resolved_cmd = command

        # 4. Check for ambiguities (e.g., multiple files matching name)
        # Extract entities from the resolved command for registration/ambiguity checking
        # (File, folder, project, app, workflow)
        temp_entities = dict(resolved_entities)
        
        # Detect candidates from command
        file_cand = self.ambiguity_resolver._extract_file_candidate(resolved_cmd)
        if file_cand and "file" not in temp_entities:
            temp_entities["file"] = file_cand
            
        wf_cand = self.ambiguity_resolver._extract_workflow_candidate(resolved_cmd)
        if wf_cand and "workflow" not in temp_entities:
            temp_entities["workflow"] = wf_cand
            
        proj_cand = self.ambiguity_resolver._extract_project_candidate(resolved_cmd)
        if proj_cand and "project" not in temp_entities:
            temp_entities["project"] = proj_cand

        app_cand = self.ambiguity_resolver._extract_app_candidate(resolved_cmd)
        if app_cand and "application" not in temp_entities:
            temp_entities["application"] = app_cand

        # Check if there is a pending clarification due to ambiguity
        pending_clar = self.ambiguity_resolver.resolve_ambiguity(
            resolved_cmd, temp_entities, state, assistant_context
        )

        if pending_clar:
            # Set the pending clarification to dialogue state and return prompt
            self.state_manager.set_pending_clarification(session_id, pending_clar)
            self.history_manager.add_turn(session_id, "user", command)
            self.history_manager.add_turn(session_id, "assistant", pending_clar.prompt)
            return BrainResponse(
                success=False,
                message=pending_clar.prompt,
                goal_name="CLARIFY",
            )

        # 5. Run standard brain pipeline execution
        self.state_manager.transition_phase(session_id, DialoguePhase.PROCESSING_TASK)
        self.history_manager.add_turn(session_id, "user", command, entities=temp_entities, resolved_objects=temp_entities)
        
        # Register entities to linker
        for etype, evalue in temp_entities.items():
            self.entity_linker.register_entity(state, etype, evalue)

        response = brain_pipeline.execute(resolved_cmd, dispatcher, context=assistant_context)

        # 6. Post-execution updates
        if response.success:
            # Update workflow, active task
            if temp_entities.get("workflow"):
                self.state_manager.set_active_workflow(session_id, temp_entities["workflow"])
            self.state_manager.transition_phase(session_id, DialoguePhase.COMPLETED)
        else:
            self.state_manager.transition_phase(session_id, DialoguePhase.IDLE)

        self.history_manager.add_turn(session_id, "assistant", response.message)
        return response
