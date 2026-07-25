"""Workflow Library subsystem managing metadata and indexing of workflows in Auralis."""

from __future__ import annotations

import logging
import time
from typing import Any, List, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from core.intents import Intent
from automation.workflow.models import WorkflowDefinition
from automation.workflow.workflow_registry import WorkflowRegistry


class WorkflowTag(BaseModel):
    """Represents a metadata categorization tag for a workflow."""

    name: str = Field(description="Name of the tag")


class WorkflowSignature(BaseModel):
    """Represents the inputs and outputs variable contract for a workflow."""

    inputs: List[str] = Field(default_factory=list, description="Expected input variables/arguments")
    outputs: List[str] = Field(default_factory=list, description="Expected output keys/variables")


class WorkflowMetadata(BaseModel):
    """Represents rich metadata details for indexing a workflow."""

    goal_name: Optional[str] = Field(None, description="Standard goal name string if mapped")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    signature: Optional[WorkflowSignature] = Field(None, description="Variable contract")
    created_at: float = Field(default_factory=time.time, description="Creation epoch timestamp")
    author: str = Field("Auralis", description="Creator identity")


class WorkflowLibrary:
    """Stores, retrieves, indexes, and queries workflows wrapped around WorkflowRegistry."""

    def __init__(
        self,
        registry: WorkflowRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the WorkflowLibrary.

        Args:
            registry: Optional custom WorkflowRegistry instance.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._registry = registry or WorkflowRegistry(logger=self._logger)
        # Store metadata mapping: workflow name -> WorkflowMetadata
        self._metadata_registry: Dict[str, WorkflowMetadata] = {}
        self._prepopulate_defaults()

    def register_workflow(
        self, workflow: WorkflowDefinition, metadata: WorkflowMetadata | None = None
    ) -> None:
        """Registers a workflow definition and its associated metadata.

        Args:
            workflow: The WorkflowDefinition model.
            metadata: Optional WorkflowMetadata model.
        """
        self._registry.register_workflow(workflow)
        meta = metadata or WorkflowMetadata()
        self._metadata_registry[workflow.name] = meta
        self._logger.info("Registered workflow in library", extra={"workflow_name": workflow.name})

    def deregister_workflow(self, name: str) -> None:
        """Deregisters a workflow by name from registry and library indexes.

        Args:
            name: Name of the workflow to remove.
        """
        # Remove from static registry dict if present
        if hasattr(self._registry, "_registry") and name in self._registry._registry:
            del self._registry._registry[name]
        # Remove from dynamic registry class-level dict if present
        if name in WorkflowRegistry._dynamic_registry:
            del WorkflowRegistry._dynamic_registry[name]
        # Remove metadata
        if name in self._metadata_registry:
            del self._metadata_registry[name]
        self._logger.info("Deregistered workflow from library", extra={"workflow_name": name})

    def get_workflow(self, name: str) -> WorkflowDefinition | None:
        """Retrieves a workflow by name.

        Args:
            name: Workflow name.

        Returns:
            The WorkflowDefinition or None if not found.
        """
        return self._registry.get_workflow(name)

    def get_metadata(self, name: str) -> WorkflowMetadata | None:
        """Retrieves metadata of a workflow.

        Args:
            name: Workflow name.

        Returns:
            The WorkflowMetadata or None if no metadata exists.
        """
        # Checks if workflow exists in registry first
        wf = self.get_workflow(name)
        if not wf:
            return None
        # Return registered metadata or default placeholder
        return self._metadata_registry.get(name) or self._metadata_registry.setdefault(name, WorkflowMetadata())

    def list_workflows(self) -> List[WorkflowDefinition]:
        """Lists all registered workflow definitions.

        Returns:
            A list of WorkflowDefinition models.
        """
        return self._registry.list_workflows()

    def lookup_by_name(self, name: str) -> List[WorkflowDefinition]:
        """Looks up workflows matching name exactly (case-insensitive).

        Args:
            name: Target workflow name.

        Returns:
            List of matching WorkflowDefinition models.
        """
        wf = self.get_workflow(name)
        if wf and wf.name.lower() == name.lower():
            return [wf]
        return []

    def lookup_by_goal(self, goal_name: str) -> List[WorkflowDefinition]:
        """Looks up workflows matching goal name exactly (case-insensitive).

        Args:
            goal_name: Target goal name.

        Returns:
            List of matching WorkflowDefinition models.
        """
        goal_upper = goal_name.upper()
        results = []
        for wf in self.list_workflows():
            meta = self.get_metadata(wf.name)
            if meta and meta.goal_name and meta.goal_name.upper() == goal_upper:
                results.append(wf)
        return results

    def lookup_by_intent(self, intent: Intent) -> List[WorkflowDefinition]:
        """Looks up workflows containing steps matching the specified system Intent.

        Args:
            intent: Target action Intent.

        Returns:
            List of matching WorkflowDefinition models.
        """
        results = []
        for wf in self.list_workflows():
            if any(step.intent == intent for step in wf.steps):
                results.append(wf)
        return results

    def lookup_by_tags(self, tags: List[str]) -> List[WorkflowDefinition]:
        """Looks up workflows containing all specified tags (case-insensitive).

        Args:
            tags: List of target tag strings.

        Returns:
            List of matching WorkflowDefinition models.
        """
        if not tags:
            return []
        tags_lower = [t.lower() for t in tags]
        results = []
        for wf in self.list_workflows():
            meta = self.get_metadata(wf.name)
            if meta and meta.tags:
                meta_tags = [t.lower() for t in meta.tags]
                if all(t in meta_tags for t in tags_lower):
                    results.append(wf)
        return results

    def _prepopulate_defaults(self) -> None:
        """Pre-populates metadata for built-in workflows inside WorkflowRegistry."""
        # Built-in: "Start Coding"
        self._metadata_registry["Start Coding"] = WorkflowMetadata(
            goal_name="START_CODING",
            tags=["code", "dev", "workspace"],
        )
        # Built-in: "Study Mode"
        self._metadata_registry["Study Mode"] = WorkflowMetadata(
            goal_name="STUDY",
            tags=["learn", "focus"],
        )
        # Built-in: "Meeting Mode"
        self._metadata_registry["Meeting Mode"] = WorkflowMetadata(
            goal_name="MEETING",
            tags=["call", "mute"],
        )
        # Built-in: "Movie Mode"
        self._metadata_registry["Movie Mode"] = WorkflowMetadata(
            goal_name="MOVIE",
            tags=["entertainment", "volume"],
        )
        # Built-in: "Clean Workspace"
        self._metadata_registry["Clean Workspace"] = WorkflowMetadata(
            goal_name="CLEAN_WORKSPACE",
            tags=["tidy", "clear"],
        )
