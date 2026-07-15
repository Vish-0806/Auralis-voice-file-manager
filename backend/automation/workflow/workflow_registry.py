"""Workflow definitions registry for system desktop workflows."""

from __future__ import annotations

import logging
from core.intents import Intent
from .models import WorkflowStep, WorkflowDefinition


class WorkflowRegistry:
    """Stores and retrieves registered workflow definitions."""

    # Class-level dictionary to hold dynamically registered task planner workflows
    _dynamic_registry: dict[str, WorkflowDefinition] = {}

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the registry and registers default built-in workflows."""

        self._logger = logger or logging.getLogger(__name__)
        self._registry: dict[str, WorkflowDefinition] = {}
        self._register_defaults()

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Registers a new workflow definition."""

        self._registry[workflow.name] = workflow
        self._logger.info("Registered workflow", extra={"workflow_name": workflow.name})

    def get_workflow(self, name: str) -> WorkflowDefinition | None:
        """Retrieves a workflow by name."""

        if name in self._dynamic_registry:
            return self._dynamic_registry[name]
        return self._registry.get(name)

    def list_workflows(self) -> list[WorkflowDefinition]:
        """Returns all registered workflow definitions."""

        built_in = list(self._registry.values())
        dynamic = list(self._dynamic_registry.values())
        return built_in + dynamic

    def _register_defaults(self) -> None:
        """Populates the registry with core built-in workflows."""

        self.register_workflow(
            WorkflowDefinition(
                name="Start Coding",
                description="Launches development tools and prepares environment.",
                steps=[
                    WorkflowStep(intent=Intent.OPEN_APPLICATION, target="VS Code"),
                    WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Terminal"),
                    WorkflowStep(intent=Intent.SET_VOLUME, target="30"),
                ],
            )
        )

        self.register_workflow(
            WorkflowDefinition(
                name="Study Mode",
                description="Optimizes settings and opens resources for focused learning.",
                steps=[
                    WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Microsoft Edge"),
                    WorkflowStep(intent=Intent.MUTE),
                    WorkflowStep(intent=Intent.ENABLE_WIFI),
                ],
            )
        )

        self.register_workflow(
            WorkflowDefinition(
                name="Meeting Mode",
                description="Prepares screen workspace and audio volumes for active meetings.",
                steps=[
                    WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Notepad"),
                    WorkflowStep(intent=Intent.MUTE),
                    WorkflowStep(intent=Intent.SHOW_DESKTOP),
                ],
            )
        )

        self.register_workflow(
            WorkflowDefinition(
                name="Movie Mode",
                description="Configures display levels and volume values for entertainment.",
                steps=[
                    WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Spotify"),
                    WorkflowStep(intent=Intent.SET_VOLUME, target="80"),
                ],
            )
        )

        self.register_workflow(
            WorkflowDefinition(
                name="Clean Workspace",
                description="Closes editing applications and tidies up active windows.",
                steps=[
                    WorkflowStep(intent=Intent.CLOSE_APPLICATION, target="Chrome"),
                    WorkflowStep(intent=Intent.CLOSE_APPLICATION, target="VS Code"),
                    WorkflowStep(intent=Intent.SHOW_DESKTOP),
                ],
            )
        )
