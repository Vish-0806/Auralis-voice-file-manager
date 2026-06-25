"""
Module: backend.core.planner

Responsibility:
    Decomposes user requests into sequential execution plan structures.
    Queries the AI Brain for intent classification and tool parameters.

This module SHOULD:
    - Inject IAgentBrain and IEventBus interfaces into its constructor.
    - Generate ExecutionPlans containing step IDs, capability tools, and arguments.
    - Publish planner activity events (e.g. AI planning lifecycle) to the EventBus.

This module should NEVER:
    - Execute capabilities, system processes, or edit files directly.
    - Import concrete model providers or connection libraries.
    - Reference hardcoded system paths.
"""

from typing import Dict, Any, List, Optional
from backend.core.interfaces import IAgentBrain
from backend.events.interfaces import IEventBus


class PlannedAction:
    """Represents a planned capability action step to be executed."""
    
    def __init__(self, step_id: int, capability: str, action: str, arguments: Dict[str, Any]) -> None:
        self.step_id: int = step_id
        self.capability: str = capability
        self.action: str = action
        self.arguments: Dict[str, Any] = arguments
        self.dependencies: List[int] = []


class ExecutionPlan:
    """A sequence of steps generated to achieve a user goal."""
    
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
    """Processes user requests into ExecutionPlans and publishes events."""
    
    def __init__(self, agent_brain: IAgentBrain, event_bus: IEventBus) -> None:
        self.agent_brain: IAgentBrain = agent_brain
        self.event_bus: IEventBus = event_bus

    def create_plan(self, user_request: str, system_context: Dict[str, Any]) -> ExecutionPlan:
        """Queries the AI Brain to build an ExecutionPlan and emits planning events."""
        pass

    def validate_plan(self, plan: ExecutionPlan, active_capabilities: List[str]) -> bool:
        """Verifies that all steps in a plan are supported by active capabilities."""
        pass
