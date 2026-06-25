"""
Module: backend.core.planner

Responsibility:
    Parses user requests into a sequence of executable capability actions.
    Builds execution plan objects containing dependency steps and parameters.

This module SHOULD:
    - Define an ExecutionPlan class that groups a list of planned actions.
    - Provide a Planner class that translates user intents and contexts into plans.
    - Support validation checks to ensure all actions match registered capabilities.

This module should NEVER:
    - Directly invoke the LLM inference wrappers.
    - Execute capabilities, files, or process commands.
    - Hardcode specific folder paths.
"""

from typing import Dict, Any, List, Optional
from backend.core.interfaces import IAgentBrain


class PlannedAction:
    """Represents a single planned capability action step."""
    
    def __init__(self, step_id: int, capability: str, action: str, arguments: Dict[str, Any]) -> None:
        self.step_id: int = step_id
        self.capability: str = capability
        self.action: str = action
        self.arguments: Dict[str, Any] = arguments
        self.dependencies: List[int] = []


class ExecutionPlan:
    """Represents a structured sequence of actions designed to achieve a user goal."""
    
    def __init__(self, plan_id: str, goal: str) -> None:
        self.plan_id: str = plan_id
        self.goal: str = goal
        self.steps: List[PlannedAction] = []
        self.current_step_index: int = 0

    def add_step(self, step: PlannedAction) -> None:
        """Appends an execution step to the plan."""
        self.steps.append(step)

    def is_completed(self) -> bool:
        """Returns True if all steps in the plan have been processed."""
        return self.current_step_index >= len(self.steps)


class Planner:
    """Generates and validates ExecutionPlans using the AI Brain."""
    
    def __init__(self, agent_brain: IAgentBrain) -> None:
        self.agent_brain: IAgentBrain = agent_brain

    def create_plan(self, user_request: str, system_context: Dict[str, Any]) -> ExecutionPlan:
        """Invokes the AI Brain to build an ExecutionPlan for a user request."""
        pass

    def validate_plan(self, plan: ExecutionPlan, active_capabilities: List[str]) -> bool:
        """Verifies that all steps in a plan are supported by active capabilities."""
        pass
