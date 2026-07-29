"""Action Planner for converting a ReasoningContext into a deterministic ActionPlan.

This module provides thread-safe action plan creation without executing commands, interacting
with the operating system, modifying files, calling LLMs, accessing memory providers,
validating plans, or resolving dependencies.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.reasoning.context_builder import ReasoningContext
from brain.reasoning.goal_extractor import GoalType

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Enumeration of deterministic execution action types."""

    LOCATE_FILES = "LOCATE_FILES"
    MOVE_FILES = "MOVE_FILES"
    COPY_FILES = "COPY_FILES"
    DELETE_FILES = "DELETE_FILES"
    RENAME_FILES = "RENAME_FILES"
    OPEN_FILE = "OPEN_FILE"
    CREATE_FOLDER = "CREATE_FOLDER"
    DELETE_FOLDER = "DELETE_FOLDER"
    SEARCH = "SEARCH"
    RESPOND = "RESPOND"
    SCHEDULE = "SCHEDULE"
    NO_ACTION = "NO_ACTION"


class ActionPriority(str, Enum):
    """Enumeration representing priority levels for action steps."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionStep(BaseModel):
    """Immutable model representing a single step within an ActionPlan."""

    model_config = ConfigDict(frozen=True)

    step_number: int
    action_type: ActionType
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: ActionPriority = ActionPriority.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionPlan(BaseModel):
    """Immutable model representing a structured sequence of execution action steps."""

    model_config = ConfigDict(frozen=True)

    request: str = ""
    goal: str = ""
    steps: List[ActionStep] = Field(default_factory=list)
    step_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionPlannerConfig(BaseModel):
    """Configuration options for ActionPlanner behavior."""

    maximum_steps: int = 100
    include_metadata: bool = True
    strict_planning: bool = True


DEFAULT_PLAN_RULES: Dict[GoalType, List[Dict[str, Any]]] = {
    GoalType.MOVE_FILES: [
        {"action_type": ActionType.LOCATE_FILES, "description": "Locate files matching criteria", "priority": ActionPriority.NORMAL},
        {"action_type": ActionType.CREATE_FOLDER, "description": "Validate destination location", "priority": ActionPriority.NORMAL},
        {"action_type": ActionType.MOVE_FILES, "description": "Move files to destination", "priority": ActionPriority.HIGH},
    ],
    GoalType.COPY_FILES: [
        {"action_type": ActionType.LOCATE_FILES, "description": "Locate files to copy", "priority": ActionPriority.NORMAL},
        {"action_type": ActionType.COPY_FILES, "description": "Copy files to target location", "priority": ActionPriority.NORMAL},
    ],
    GoalType.DELETE_FILES: [
        {"action_type": ActionType.LOCATE_FILES, "description": "Locate target files for deletion", "priority": ActionPriority.NORMAL},
        {"action_type": ActionType.DELETE_FILES, "description": "Delete specified files", "priority": ActionPriority.HIGH},
    ],
    GoalType.RENAME_FILES: [
        {"action_type": ActionType.LOCATE_FILES, "description": "Locate target file", "priority": ActionPriority.NORMAL},
        {"action_type": ActionType.RENAME_FILES, "description": "Rename file to target name", "priority": ActionPriority.NORMAL},
    ],
    GoalType.SEARCH_FILES: [
        {"action_type": ActionType.SEARCH, "description": "Search for files matching constraints", "priority": ActionPriority.NORMAL},
    ],
    GoalType.OPEN_FILE: [
        {"action_type": ActionType.LOCATE_FILES, "description": "Locate specified file", "priority": ActionPriority.NORMAL},
        {"action_type": ActionType.OPEN_FILE, "description": "Open target file with default handler", "priority": ActionPriority.NORMAL},
    ],
    GoalType.CREATE_FOLDER: [
        {"action_type": ActionType.CREATE_FOLDER, "description": "Create folder at target path", "priority": ActionPriority.NORMAL},
    ],
    GoalType.DELETE_FOLDER: [
        {"action_type": ActionType.DELETE_FOLDER, "description": "Delete folder at specified location", "priority": ActionPriority.HIGH},
    ],
    GoalType.SCHEDULE_TASK: [
        {"action_type": ActionType.SCHEDULE, "description": "Schedule background recurring task", "priority": ActionPriority.NORMAL},
    ],
    GoalType.ANSWER_QUESTION: [
        {"action_type": ActionType.RESPOND, "description": "Generate direct informational response", "priority": ActionPriority.NORMAL},
    ],
    GoalType.GENERAL_TASK: [
        {"action_type": ActionType.LOCATE_FILES, "description": "Locate task inputs", "priority": ActionPriority.NORMAL},
        {"action_type": ActionType.RESPOND, "description": "Execute generic task workflow", "priority": ActionPriority.NORMAL},
    ],
    GoalType.UNKNOWN: [
        {"action_type": ActionType.NO_ACTION, "description": "No action required for unknown goal", "priority": ActionPriority.LOW},
    ],
}


class ActionPlanner:
    """Thread-safe engine for converting a ReasoningContext into a deterministic ActionPlan."""

    def __init__(self, config: Optional[ActionPlannerConfig] = None) -> None:
        """Initializes the ActionPlanner with optional configuration and thread lock."""
        self.config = config or ActionPlannerConfig()
        self._plan_rules: Dict[GoalType, List[Dict[str, Any]]] = {}
        self._lock = threading.RLock()

        # Pre-populate default plan rules
        for goal_type, rules in DEFAULT_PLAN_RULES.items():
            self._plan_rules[goal_type] = [dict(r) for r in rules]

    def register_plan_rule(
        self,
        goal_type: GoalType,
        steps_template: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a custom plan rule template for a GoalType."""
        with self._lock:
            self._plan_rules[goal_type] = [dict(s) for s in steps_template]
            logger.info("Plan Rule Registered: goal_type=%s", goal_type)
            return True

    def remove_plan_rule(self, goal_type: GoalType) -> bool:
        """Removes a registered plan rule template for a GoalType."""
        with self._lock:
            if goal_type in self._plan_rules:
                del self._plan_rules[goal_type]
                logger.info("Plan Rule Removed: goal_type=%s", goal_type)
                return True
            return False

    def clear_plan_rules(self) -> None:
        """Clears all plan rules from the registry."""
        with self._lock:
            self._plan_rules.clear()
            logger.info("Plan Registry Cleared")

    def create_plan(self, context: Optional[ReasoningContext] = None) -> ActionPlan:
        """Deterministically creates an ActionPlan from a ReasoningContext."""
        with self._lock:
            now = datetime.now(timezone.utc)
            if not isinstance(context, ReasoningContext):
                fallback_step = ActionStep(
                    step_number=1,
                    action_type=ActionType.NO_ACTION,
                    description="No action for invalid context",
                    priority=ActionPriority.LOW,
                )
                plan = ActionPlan(
                    request="",
                    goal=GoalType.UNKNOWN.value,
                    steps=[fallback_step],
                    step_count=1,
                    created_at=now,
                    metadata={},
                )
                logger.info("Action Plan Created: step_count=1")
                return plan

            goal_type = context.goal.goal_type
            template_steps = self._plan_rules.get(goal_type)

            if not template_steps:
                template_steps = [
                    {
                        "action_type": ActionType.NO_ACTION,
                        "description": f"No action template for goal {goal_type}",
                        "priority": ActionPriority.LOW,
                    }
                ]

            generated_steps: List[ActionStep] = []
            for idx, t in enumerate(template_steps, start=1):
                if idx > self.config.maximum_steps:
                    break
                step = ActionStep(
                    step_number=idx,
                    action_type=t["action_type"],
                    description=t.get("description", ""),
                    parameters=t.get("parameters", {}),
                    priority=t.get("priority", ActionPriority.NORMAL),
                    metadata=t.get("metadata", {}),
                )
                generated_steps.append(step)

            metadata = dict(context.metadata) if self.config.include_metadata else {}

            plan = ActionPlan(
                request=context.request,
                goal=context.goal.goal_type.value,
                steps=generated_steps,
                step_count=len(generated_steps),
                created_at=now,
                metadata=metadata,
            )
            logger.info("Action Plan Created")
            return plan

    def list_plan_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Lists all registered plan rule templates."""
        with self._lock:
            return {k.value: [dict(s) for s in v] for k, v in self._plan_rules.items()}
