"""AI Brain Controller orchestrator coordinating the complete AI pipeline in Auralis."""

from __future__ import annotations

import logging
import uuid
import time
from typing import Any

from memory import MemoryService

from brain.goal.goal_interpreter import GoalInterpreter
from brain.reasoning.reasoning_engine import ReasoningEngine
from brain.planning.task_planner import TaskPlanner
from brain.capability.capability_selector import CapabilitySelector
from brain.execution.execution_engine import ExecutionEngine
from brain.recovery.recovery_engine import RecoveryEngine
from brain.monitoring.progress_monitor import ProgressMonitor

from .models import BrainRequest, BrainResponse, BrainStatus, BrainExecution
from .brain_config import BrainConfig
from .brain_registry import BrainRegistry
from .brain_pipeline import BrainPipeline


class BrainController:
    """Coordinates and manages subsystems of the local-first AI Brain."""

    def __init__(
        self,
        config: BrainConfig | None = None,
        registry: BrainRegistry | None = None,
        logger: logging.Logger | None = None,
        memory_service: MemoryService | None = None,
    ) -> None:
        """Initializes the BrainController.

        Args:
            config: Configured BrainConfig parameters.
            registry: Configured dynamic BrainRegistry mapping.
            logger: Optional custom logger.
            memory_service: Optional injected MemoryService instance.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._config = config or BrainConfig()
        self._registry = registry or BrainRegistry(logger=self._logger)
        self._memory_service = memory_service or MemoryService()
        self._active_executions: dict[str, BrainExecution] = {}
        self._register_subsystems()

    def _run_async(self, coro) -> Any:
        """Runs a coroutine synchronously or schedules it on a running event loop."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            return loop.create_task(coro)
        else:
            return loop.run_until_complete(coro)

    def process_request(self, request: BrainRequest, dispatcher: Any) -> BrainResponse:
        """Runs the request through the registered pipeline.

        Args:
            request: The incoming BrainRequest.
            dispatcher: ActionDispatcher instance.

        Returns:
            A BrainResponse detailing outcomes.
        """
        execution_id = request.correlation_id or f"exec_{uuid.uuid4().hex[:8]}"
        self._logger.info("Controller received brain request processing trigger", extra={"execution_id": execution_id})

        # Save incoming conversation prompt to memory
        from memory.models.domain_models import MemoryEntry, MemoryType, MemoryMetadata
        user_entry = MemoryEntry(
            id=execution_id + "_user",
            content=request.message,
            memory_type=MemoryType.CONVERSATION,
            metadata=MemoryMetadata(
                additional_info={
                    "session_id": request.correlation_id or "default",
                    "role": "user",
                }
            )
        )
        self._run_async(self._memory_service.save(user_entry))

        execution = BrainExecution(
            execution_id=execution_id,
            status=BrainStatus.PROCESSING,
            start_time=time.time(),
        )
        self._active_executions[execution_id] = execution

        # Resolve user_id from context if available, otherwise default to active provider's default user_id or 1
        user_id = 1
        if request.context and "user_id" in request.context:
            user_id = int(request.context["user_id"])
        elif request.context and "userId" in request.context:
            user_id = int(request.context["userId"])
        else:
            try:
                provider = self._memory_service._manager._repository._provider
                if hasattr(provider, "_default_user_id") and provider._default_user_id is not None:
                    user_id = provider._default_user_id
            except Exception:
                pass

        self._logger.info("Context retrieval started", extra={"execution_id": execution_id})
        try:
            from memory.manager.context_builder import ContextBuilder
            builder = ContextBuilder(self._memory_service)
            session_id = request.correlation_id or "default"
            assistant_context = self._run_async(builder.build_context(user_id=user_id, session_id=session_id, query_text=request.message))
            self._logger.info(
                f"Context retrieval completed. Loaded {len(assistant_context.recent_conversations)} conversations and {len(assistant_context.recent_executions)} executions.",
                extra={
                    "execution_id": execution_id,
                    "conversations_count": len(assistant_context.recent_conversations),
                    "executions_count": len(assistant_context.recent_executions),
                }
            )
        except Exception:
            self._logger.warning(
                "Failed to build AssistantContext; continuing with empty context",
                exc_info=True,
                extra={"execution_id": execution_id}
            )
            from memory import AssistantContext
            assistant_context = AssistantContext()
            self._logger.info(
                "Context retrieval completed. Loaded 0 conversations and 0 executions.",
                extra={
                    "execution_id": execution_id,
                    "conversations_count": 0,
                    "executions_count": 0,
                }
            )

        # Resolve references using ReferenceResolver
        try:
            from brain.planning.reference_resolver import ReferenceResolver
            resolver = ReferenceResolver()
            resolved_req = resolver.resolve(request.message, assistant_context)
            resolved_message = resolved_req.resolved_request
            self._logger.info(
                "Reference resolution completed",
                extra={
                    "execution_id": execution_id,
                    "original_request": request.message,
                    "resolved_request": resolved_message,
                    "entities": resolved_req.resolved_entities,
                    "confidence": resolved_req.confidence_score,
                }
            )
        except Exception:
            self._logger.warning(
                "Failed to run ReferenceResolver; falling back to original request",
                exc_info=True,
                extra={"execution_id": execution_id}
            )
            resolved_message = request.message

        pipeline = BrainPipeline(
            config=self._config,
            interpreter=self._registry.get_module("GoalInterpreter"),
            reasoning_engine=self._registry.get_module("ReasoningEngine"),
            planner=self._registry.get_module("TaskPlanner"),
            capability_selector=self._registry.get_module("CapabilitySelector"),
            execution_engine=self._registry.get_module("ExecutionEngine"),
            logger=self._logger,
        )

        execution.status = BrainStatus.EXECUTING
        response = pipeline.execute(resolved_message, dispatcher, context=assistant_context)

        execution.status = BrainStatus.COMPLETED if response.success else BrainStatus.FAILED
        execution.end_time = time.time()

        self._logger.info(
            "Controller completed request pipeline execution",
            extra={"execution_id": execution_id, "status": execution.status.value},
        )

        # Save outgoing conversation reply to memory
        from memory.models.domain_models import MemoryEntry, MemoryType, MemoryMetadata
        assistant_entry = MemoryEntry(
            id=execution_id + "_assistant",
            content=response.message,
            memory_type=MemoryType.CONVERSATION,
            metadata=MemoryMetadata(
                additional_info={
                    "session_id": request.correlation_id or "default",
                    "role": "assistant",
                }
            )
        )
        self._run_async(self._memory_service.save(assistant_entry))

        # Save activity execution history to memory
        activity_entry = MemoryEntry(
            id=execution_id + "_activity",
            content=f"Execution completed for goal {response.goal_name}",
            memory_type=MemoryType.ACTIVITY,
            metadata=MemoryMetadata(
                additional_info={
                    "status": execution.status.value,
                    "duration_ms": int((execution.end_time - execution.start_time) * 1000),
                    "input_parameters": {"message": request.message},
                    "output_result": {"success": response.success, "message": response.message},
                }
            )
        )
        self._run_async(self._memory_service.save(activity_entry))

        return response

    def get_execution_status(self, execution_id: str) -> BrainStatus:
        """Retrieves status for a registered run ID."""
        run = self._active_executions.get(execution_id)
        return run.status if run else BrainStatus.IDLE

    def _register_subsystems(self) -> None:
        """Registers Auralis subsystems into the registry."""
        self._registry.register_module(
            "GoalInterpreter",
            GoalInterpreter(logger=self._logger),
        )
        self._registry.register_module(
            "ReasoningEngine",
            ReasoningEngine(logger=self._logger),
        )
        self._registry.register_module(
            "TaskPlanner",
            TaskPlanner(logger=self._logger),
        )
        self._registry.register_module(
            "CapabilitySelector",
            CapabilitySelector(logger=self._logger),
        )
        recovery_engine = RecoveryEngine(logger=self._logger)
        self._registry.register_module("RecoveryEngine", recovery_engine)

        progress_monitor = ProgressMonitor(logger=self._logger)
        self._registry.register_module("ProgressMonitor", progress_monitor)

        execution_engine = ExecutionEngine(
            recovery_engine=recovery_engine,
            progress_monitor=progress_monitor,
            logger=self._logger,
        )
        self._registry.register_module("ExecutionEngine", execution_engine)
