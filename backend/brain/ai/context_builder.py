"""ContextBuilder for constructing AIContext objects (Phase 10.1).

Assembles conversation history, memory context, workspace context,
current request parameters, and execution state into an AIContext model.
"""

import uuid
from typing import Any, Dict, List, Optional

from brain.ai.exceptions import ContextBuildError
from brain.ai.interfaces import ContextBuilder
from brain.ai.ai_models import AIContext
from brain.runtime.brain_models import BrainRequest


class DefaultContextBuilder(ContextBuilder):
    """Default implementation of ContextBuilder interface."""

    def build_context(
        self,
        request: BrainRequest,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        memory_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> AIContext:
        """Assemble structured AIContext snapshot from inputs.

        Args:
            request: Incoming BrainRequest model.
            conversation_history: Optional list of past messages.
            memory_context: Optional memory items / preferences dictionary.
            workspace_context: Optional project workspace metadata.
            execution_context: Optional active execution runtime state.

        Returns:
            Constructed AIContext model instance.

        Raises:
            ContextBuildError: If context assembly encounters invalid data.
        """
        try:
            # TODO: Integrate with backend.memory context retrieval engine
            resolved_memory = memory_context if memory_context is not None else {}

            # TODO: Integrate with backend.os / workspace resolution engine
            resolved_workspace = workspace_context if workspace_context is not None else {}

            # TODO: Integrate with backend.brain.conversation history manager
            resolved_history = conversation_history if conversation_history is not None else []

            # TODO: Integrate with backend.brain.execution runtime state
            resolved_execution = execution_context if execution_context is not None else {}

            req_id = request.request_id if request.request_id else f"req-{uuid.uuid4().hex[:8]}"

            return AIContext(
                request_id=req_id,
                session_id=request.session_id,
                conversation_id=request.conversation_id,
                raw_query=request.raw_text,
                conversation_history=resolved_history,
                memory_context=resolved_memory,
                workspace_context=resolved_workspace,
                execution_context=resolved_execution,
                metadata={
                    "built_by": "DefaultContextBuilder",
                    "request_type": getattr(request, "request_type", "general"),
                },
            )
        except Exception as exc:
            raise ContextBuildError(f"Failed to build AIContext: {exc}") from exc
