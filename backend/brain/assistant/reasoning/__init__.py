"""Decision & Reasoning Coordinator Subsystem for Auralis (Phase 13.4).

Coordinates high-level decision making and routing between Assistant Runtime, Dialogue Runtime,
AI Runtime, and Execution Runtime without executing LLM calls or OS commands.
"""

from brain.assistant.reasoning.decision_coordinator import DecisionCoordinator
from brain.assistant.reasoning.decision_evaluator import DecisionEvaluator
from brain.assistant.reasoning.decision_provider import DecisionProvider
from brain.assistant.reasoning.decision_runtime import DecisionRuntime
from brain.assistant.reasoning.exceptions import (
    DecisionException,
    DecisionPolicyError,
    DecisionRoutingError,
    DecisionRuntimeError,
    DecisionValidationError,
)
from brain.assistant.reasoning.interfaces import (
    IDecisionCoordinator,
    IDecisionEvaluator,
    IDecisionPolicyManager,
    IDecisionProvider,
    IDecisionRuntime,
)
from brain.assistant.reasoning.models import (
    DecisionAction,
    DecisionCandidate,
    DecisionContext,
    DecisionHealth,
    DecisionMetadata,
    DecisionOutcome,
    DecisionPolicy,
    DecisionPriority,
    DecisionRequest,
    DecisionResult,
    DecisionStatistics,
)
from brain.assistant.reasoning.policy_manager import PolicyManager
from brain.assistant.reasoning.runtime import (
    get_decision_runtime,
    reset_decision_runtime,
)

__all__ = [
    # Enums & Models
    "DecisionAction",
    "DecisionPriority",
    "DecisionOutcome",
    "DecisionMetadata",
    "DecisionPolicy",
    "DecisionContext",
    "DecisionRequest",
    "DecisionCandidate",
    "DecisionResult",
    "DecisionStatistics",
    "DecisionHealth",
    # Exceptions
    "DecisionException",
    "DecisionValidationError",
    "DecisionPolicyError",
    "DecisionRoutingError",
    "DecisionRuntimeError",
    # Interfaces
    "IDecisionCoordinator",
    "IDecisionPolicyManager",
    "IDecisionEvaluator",
    "IDecisionProvider",
    "IDecisionRuntime",
    # Components & Managers
    "DecisionCoordinator",
    "PolicyManager",
    "DecisionEvaluator",
    "DecisionProvider",
    "DecisionRuntime",
    # Singleton accessors
    "get_decision_runtime",
    "reset_decision_runtime",
]
