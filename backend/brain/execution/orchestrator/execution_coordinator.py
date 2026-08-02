"""Execution Coordinator for the Auralis Command Execution Orchestrator (Phase 12.3).

Responsible for:
- evaluating incoming requests or IntentResolution objects
- determining whether workflow planning is required
- selecting execution mode (DIRECT, PLANNED, AI_GUIDED, INTERACTIVE, CRITICAL)
- building the immutable ExecutionContext
- assigning execution priority (LOW, NORMAL, HIGH, CRITICAL)
"""

from typing import Any, Dict, Optional

from brain.execution.orchestrator.exceptions import ExecutionPreparationError
from brain.execution.orchestrator.interfaces import IExecutionCoordinator
from brain.execution.orchestrator.orchestrator_models import (
    ExecutionContext,
    ExecutionMode,
    ExecutionPriority,
    ExecutionRequest,
    ExecutionState,
)


class ExecutionCoordinator(IExecutionCoordinator):
    """Coordinator evaluating execution requests, determining modes, and building ExecutionContext."""

    def prepare_execution(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionContext:
        """Prepare an ExecutionContext from a prompt string, IntentResolution, or ExecutionRequest.

        Args:
            request_or_prompt: ExecutionRequest, IntentResolution, dict, or prompt string.
            context: Optional contextual parameters.

        Returns:
            Populated ExecutionContext object.

        Raises:
            ExecutionPreparationError: If request is None or invalid.
        """
        if request_or_prompt is None:
            raise ExecutionPreparationError("Execution request or prompt cannot be None")

        raw_prompt = ""
        intent_res = None
        mode = ExecutionMode.DIRECT
        priority = ExecutionPriority.NORMAL
        ctx_meta = dict(context or {})

        if isinstance(request_or_prompt, ExecutionRequest):
            return ExecutionContext(
                request=request_or_prompt,
                state=ExecutionState.PREPARING,
                metadata=ctx_meta,
            )

        if isinstance(request_or_prompt, str):
            raw_prompt = request_or_prompt
        elif hasattr(request_or_prompt, "primary_intent"):  # IntentResolution
            intent_res = request_or_prompt
            if intent_res.primary_intent:
                raw_prompt = intent_res.primary_intent.raw_prompt
        elif isinstance(request_or_prompt, dict):
            raw_prompt = request_or_prompt.get("prompt", "")
            ctx_meta.update(request_or_prompt.get("context", {}))
        else:
            raw_prompt = str(request_or_prompt)

        # Determine mode & planning requirement
        lower_prompt = raw_prompt.lower()
        if any(w in lower_prompt for w in ["workflow", "pipeline", "multi-step", "plan", "sequence", "schedule"]):
            mode = ExecutionMode.PLANNED
            priority = ExecutionPriority.HIGH
        elif any(w in lower_prompt for w in ["shutdown", "reboot", "format", "delete root", "kill -9"]):
            mode = ExecutionMode.CRITICAL
            priority = ExecutionPriority.CRITICAL
        elif any(w in lower_prompt for w in ["generate", "summarize", "write code", "explain"]):
            mode = ExecutionMode.AI_GUIDED
            priority = ExecutionPriority.NORMAL
        else:
            mode = ExecutionMode.DIRECT
            priority = ExecutionPriority.NORMAL

        req = ExecutionRequest(
            raw_prompt=raw_prompt,
            intent_resolution=intent_res,
            mode=mode,
            priority=priority,
            context=ctx_meta,
        )

        return ExecutionContext(
            request=req,
            state=ExecutionState.PREPARING,
            metadata={"mode_determined": mode.value, "priority_assigned": priority.value},
        )
