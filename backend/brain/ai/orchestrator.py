"""AIOrchestrator for managing end-to-end AI completion workflows (Phase 10.1).

Execution sequence:
receive BrainRequest
↓
build context (ContextBuilder)
↓
build prompt (PromptBuilder)
↓
select provider (ProviderManager)
↓
receive AI response (AIProvider)
↓
return BrainResponse
"""

import uuid
from typing import Any, Dict, Optional

from brain.ai.exceptions import AIOrchestrationError, ProviderUnavailableError
from brain.ai.interfaces import ContextBuilder, PromptBuilder, ToolRouter
from brain.ai.context_builder import DefaultContextBuilder
from brain.ai.prompt_engine import DefaultPromptBuilder
from brain.ai.tool_router import DefaultToolRouter
from brain.ai.provider_manager import ProviderManager
from brain.ai.ai_models import AIRequest, FinishReason
from brain.runtime.brain_models import BrainRequest, BrainResponse, PipelineStatus


class AIOrchestrator:
    """Orchestrator that ties together ContextBuilder, PromptBuilder, ProviderManager, and ToolRouter."""

    def __init__(
        self,
        provider_manager: Optional[ProviderManager] = None,
        context_builder: Optional[ContextBuilder] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        tool_router: Optional[ToolRouter] = None,
    ) -> None:
        self.provider_manager = provider_manager or ProviderManager()
        self.context_builder = context_builder or DefaultContextBuilder()
        self.prompt_builder = prompt_builder or DefaultPromptBuilder()
        self.tool_router = tool_router or DefaultToolRouter()

    def process_request(
        self,
        request: BrainRequest,
        provider_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> BrainResponse:
        """Execute the AI completion workflow for an incoming BrainRequest.

        Args:
            request: Incoming BrainRequest model.
            provider_name: Optional name of specific provider to use.
            parameters: Optional parameter overrides for completion generation.

        Returns:
            BrainResponse wrapping AI response or error message.

        Raises:
            AIOrchestrationError: If unrecoverable pipeline failure occurs.
        """
        req_id = request.request_id if request.request_id else f"req-{uuid.uuid4().hex[:8]}"

        try:
            # 1. Build context
            # TODO: Add rich context resolution logic in Phase 10.2+
            ai_context = self.context_builder.build_context(request)

            # 2. Build prompt
            # TODO: Add dynamic prompt rendering logic in Phase 10.2+
            prompt = self.prompt_builder.build_prompt(ai_context)

            # 3. Select provider
            # TODO: Add fallback/retry provider selection in Phase 10.2+
            if provider_name:
                provider = self.provider_manager.get_provider(provider_name)
            else:
                provider = self.provider_manager.get_active_provider()

            if provider is None:
                return BrainResponse(
                    request_id=req_id,
                    success=False,
                    pipeline_status=PipelineStatus.FAILED,
                    text="",
                    error="No active AI provider registered.",
                    execution_summary={
                        "step": "provider_selection",
                        "status": "failed",
                        "error": "No registered active provider available.",
                    },
                )

            if not provider.is_available():
                raise ProviderUnavailableError(provider.get_info().name)

            # 4. Gather registered tool schemas
            available_tools = self.tool_router.get_available_tools()

            # 5. Build AIRequest
            ai_request = AIRequest(
                request_id=req_id,
                prompt=prompt,
                tools=available_tools,
                parameters=parameters or {},
                provider_name=provider.get_info().name,
            )

            # 6. Generate AI response
            # TODO: Concrete provider execution in Phase 10.2+
            ai_response = provider.generate_response(ai_request)

            # 7. Process tool calls if present
            # TODO: Route tool calls through self.tool_router in Phase 10.2+
            if ai_response.finish_reason == FinishReason.TOOL_CALLS:
                for tool_call in ai_response.tool_calls:
                    self.tool_router.route_tool_call(tool_call)

            # 8. Construct and return BrainResponse
            return BrainResponse(
                request_id=req_id,
                success=True,
                pipeline_status=PipelineStatus.COMPLETED,
                text=ai_response.text,
                execution_summary={
                    "step": "ai_completion",
                    "provider": ai_response.provider_name,
                    "finish_reason": ai_response.finish_reason,
                    "tool_calls_count": len(ai_response.tool_calls),
                },
            )
        except Exception as exc:
            raise AIOrchestrationError(f"AIOrchestrator pipeline failed: {exc}") from exc
