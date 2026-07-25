"""Workflow Composer subsystem merging workflows and steps in Auralis."""

from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Set
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from core.intents import Intent
from automation.workflow.models import WorkflowStep, WorkflowDefinition
from .models import ExecutionStep, ExecutionDependency, ExecutionSequence
from .dependency_resolver import DependencyResolver


class WorkflowMergeConflict(BaseModel):
    """Represents a conflict detected during workflow composition."""

    conflict_type: str = Field(
        description="Type of conflict: 'exclusive_action', 'conflicting_parameters', or 'ordering'"
    )
    step_id: str = Field(description="ID or Intent of the step involved in the conflict")
    message: str = Field(description="Detailed description of the merge conflict")


class WorkflowCompositionResult(BaseModel):
    """Represents the results of composing workflows and steps."""

    merged_workflow: Optional[WorkflowDefinition] = Field(
        None, description="The compiled composite WorkflowDefinition model"
    )
    conflicts: List[WorkflowMergeConflict] = Field(
        default_factory=list, description="List of detected merge conflicts"
    )
    reused_workflows: List[str] = Field(
        default_factory=list, description="Names of library workflows reused in the merge"
    )
    generated_workflows: List[str] = Field(
        default_factory=list, description="Names of compiled composite workflows"
    )


class WorkflowComposition(BaseModel):
    """Represents the composition query payload."""

    name: str = Field(description="Name of the target workflow to produce")
    description: str = Field(description="Description of the target workflow")
    workflows: List[WorkflowDefinition] = Field(
        default_factory=list, description="List of library workflows to merge"
    )
    steps: List[ExecutionStep] = Field(
        default_factory=list, description="List of dynamic execution steps to merge"
    )


class WorkflowComposer:
    """Combines multiple workflows and dynamic steps, resolving conflicts and parameters."""

    def __init__(
        self,
        dependency_resolver: DependencyResolver | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the WorkflowComposer.

        Args:
            dependency_resolver: Custom dependency resolver for cycle checks.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._resolver = dependency_resolver or DependencyResolver(logger=self._logger)

    def compose(self, composition: WorkflowComposition) -> WorkflowCompositionResult:
        """Merges matched workflows and steps into a single WorkflowDefinition.

        Args:
            composition: WorkflowComposition input.

        Returns:
            WorkflowCompositionResult outlining merged model or merge conflicts.
        """
        self._logger.info(
            "Composing workflows and steps",
            extra={
                "composition_name": composition.name,
                "workflows_count": len(composition.workflows),
                "steps_count": len(composition.steps),
            },
        )

        conflicts: List[WorkflowMergeConflict] = []
        reused_names = [wf.name for wf in composition.workflows]

        # 1. Convert all steps to unified ExecutionStep structures
        unified_steps: Dict[str, ExecutionStep] = {}
        # Track implicit dependencies: child_id -> set of parent_ids
        dependencies_map: Dict[str, Set[str]] = {}

        # Translate dynamic steps first
        for step in composition.steps:
            step_id = step.step_id
            if step_id in unified_steps:
                # Merge duplicate step parameters
                existing = unified_steps[step_id]
                self._merge_parameters(existing, step, conflicts)
            else:
                unified_steps[step_id] = step.model_copy(deep=True)
            dependencies_map.setdefault(step_id, set())

        # Translate library workflows
        for wf_idx, wf in enumerate(composition.workflows):
            prev_step_id: Optional[str] = None
            for step_idx, w_step in enumerate(wf.steps):
                # Standard step ID: wf_{wf_idx}_step_{step_idx}_{intent}
                step_id = f"wf_{wf_idx}_step_{step_idx}_{w_step.intent.value}"
                
                # Convert to ExecutionStep
                e_step = ExecutionStep(
                    step_id=step_id,
                    intent=w_step.intent,
                    target=w_step.target,
                    parameters=w_step.parameters,
                )
                
                unified_steps[step_id] = e_step
                dependencies_map.setdefault(step_id, set())
                
                # Sequential dependency within workflow
                if prev_step_id:
                    dependencies_map[step_id].add(prev_step_id)
                prev_step_id = step_id

        # 2. Check for exclusive action / duplicate exclusive parameter conflicts
        self._check_exclusive_conflicts(list(unified_steps.values()), conflicts)

        if conflicts:
            return WorkflowCompositionResult(
                merged_workflow=None,
                conflicts=conflicts,
                reused_workflows=reused_names,
                generated_workflows=[],
            )

        # 3. Formulate sequence and check ordering conflicts via topological sort
        deps_list: List[ExecutionDependency] = []
        for s_id, parents in dependencies_map.items():
            if parents:
                deps_list.append(
                    ExecutionDependency(step_id=s_id, depends_on=list(parents))
                )

        seq = ExecutionSequence(steps=list(unified_steps.values()), dependencies=deps_list)

        try:
            ordered_steps = self._resolver.resolve_order(seq)
        except ValueError as exc:
            conflicts.append(
                WorkflowMergeConflict(
                    conflict_type="ordering",
                    step_id="sequence_cycle",
                    message=f"Circular dependency cycle detected in merge: {str(exc)}",
                )
            )
            return WorkflowCompositionResult(
                merged_workflow=None,
                conflicts=conflicts,
                reused_workflows=reused_names,
                generated_workflows=[],
            )

        # 4. Map back to WorkflowStep structures
        final_workflow_steps = [
            WorkflowStep(
                intent=s.intent,
                target=s.target,
                parameters=s.parameters,
            )
            for s in ordered_steps
        ]

        merged_wf = WorkflowDefinition(
            name=composition.name,
            description=composition.description,
            steps=final_workflow_steps,
        )

        return WorkflowCompositionResult(
            merged_workflow=merged_wf,
            conflicts=[],
            reused_workflows=reused_names,
            generated_workflows=[composition.name],
        )

    def _merge_parameters(
        self, existing: ExecutionStep, new_step: ExecutionStep, conflicts: List[WorkflowMergeConflict]
    ) -> None:
        """Merges target and parameter payloads, raising conflicts on differences."""
        if existing.target != new_step.target:
            conflicts.append(
                WorkflowMergeConflict(
                    conflict_type="conflicting_parameters",
                    step_id=existing.step_id,
                    message=f"Conflicting target value: '{existing.target}' vs '{new_step.target}'",
                )
            )
            return

        for k, v in new_step.parameters.items():
            if k in existing.parameters and existing.parameters[k] != v:
                conflicts.append(
                    WorkflowMergeConflict(
                        conflict_type="conflicting_parameters",
                        step_id=existing.step_id,
                        message=f"Conflicting parameter key '{k}': '{existing.parameters[k]}' vs '{v}'",
                    )
                )
            else:
                existing.parameters[k] = v

    def _check_exclusive_conflicts(
        self, steps: List[ExecutionStep], conflicts: List[WorkflowMergeConflict]
    ) -> None:
        """Detects contradictions between singular/exclusive actions."""
        # Find all volume steps
        volume_steps = [s for s in steps if s.intent == Intent.SET_VOLUME]
        if len(volume_steps) > 1:
            targets = {s.target for s in volume_steps}
            if len(targets) > 1:
                conflicts.append(
                    WorkflowMergeConflict(
                        conflict_type="conflicting_parameters",
                        step_id="SET_VOLUME",
                        message=f"Conflicting target volumes detected: {', '.join(str(t) for t in targets)}",
                    )
                )

        lock_steps = [s for s in steps if s.intent == Intent.LOCK_PC]
        app_steps = [s for s in steps if s.intent == Intent.OPEN_APPLICATION]
        if lock_steps and app_steps:
            conflicts.append(
                WorkflowMergeConflict(
                    conflict_type="exclusive_action",
                    step_id="LOCK_PC",
                    message="Cannot perform open application actions while locking the computer.",
                )
            )
