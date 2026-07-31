"""DefaultToolExecutor implementation for validating and executing AI tool calls (Phase 10.4).

Responsibilities:
- Validate tool presence and schema parameters
- Execute tool logic
- Capture execution latency
- Handle and log exceptions
- Generate structured ToolResult objects
- Support sequential batch execution without stopping on single tool failures
"""

import time
import logging
from typing import Any, Dict, List, Optional

from brain.ai.ai_models import ToolCall, ToolResult
from brain.ai.tools.exceptions import (
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
)
from brain.ai.tools.interfaces import ToolExecutorInterface, ToolRegistryInterface
from brain.ai.tools.registry import DefaultToolRegistry

logger = logging.getLogger(__name__)


class DefaultToolExecutor(ToolExecutorInterface):
    """Execution engine for validating and executing tool calls against a ToolRegistry."""

    def __init__(self, registry: Optional[ToolRegistryInterface] = None) -> None:
        self.registry = registry or DefaultToolRegistry()

    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Validate and execute a single ToolCall object.

        Args:
            tool_call: ToolCall model instance.

        Returns:
            ToolResult object containing status, output, execution time, or error details.
        """
        start_time = time.perf_counter()
        tool_name = tool_call.tool_name

        try:
            # 1. Lookup tool in registry
            tool = self.registry.get_tool(tool_name)
            metadata = tool.get_metadata()

            # 2. Check enabled status
            if not metadata.enabled:
                raise ToolValidationError(tool_name, reason=f"Tool '{tool_name}' is currently disabled.")

            # 3. Validate arguments against schema required parameters
            self._validate_arguments(tool_call.arguments, metadata.parameters, tool_name)

            # 4. Execute tool logic
            output = tool.execute(tool_call.arguments)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                f"Tool Execution Success | Tool: '{tool_name}' | "
                f"CallID: '{tool_call.call_id}' | Latency: {elapsed_ms}ms"
            )

            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_name,
                success=True,
                output=output,
                error_message=None,
                execution_time_ms=elapsed_ms,
            )

        except ToolNotFoundError as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(
                f"Tool Execution Failure | Tool: '{tool_name}' not found | "
                f"CallID: '{tool_call.call_id}' | Latency: {elapsed_ms}ms"
            )
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_name,
                success=False,
                output=None,
                error_message=str(exc),
                execution_time_ms=elapsed_ms,
            )

        except (ToolValidationError, ToolExecutionError) as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Tool Execution Failure | Tool: '{tool_name}' | "
                f"Reason: {exc} | CallID: '{tool_call.call_id}' | Latency: {elapsed_ms}ms"
            )
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_name,
                success=False,
                output=None,
                error_message=str(exc),
                execution_time_ms=elapsed_ms,
            )

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Tool Execution Failure | Tool: '{tool_name}' unhandled exception | "
                f"Error: {exc} | CallID: '{tool_call.call_id}' | Latency: {elapsed_ms}ms"
            )
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_name,
                success=False,
                output=None,
                error_message=f"Unhandled tool execution error: {exc}",
                execution_time_ms=elapsed_ms,
            )

    def execute_multiple(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute multiple ToolCall objects sequentially without stopping on individual failures.

        Args:
            tool_calls: List of ToolCall objects.

        Returns:
            List of ToolResult objects for all executed tool calls.
        """
        results: List[ToolResult] = []
        if not tool_calls:
            return results

        logger.info(f"Starting batch tool execution for {len(tool_calls)} tool calls.")

        for call in tool_calls:
            res = self.execute_tool_call(call)
            results.append(res)

        return results

    def _validate_arguments(
        self,
        arguments: Dict[str, Any],
        parameters_schema: Dict[str, Any],
        tool_name: str,
    ) -> None:
        """Validate required properties specified in JSON schema."""
        if not parameters_schema:
            return

        required_fields = parameters_schema.get("required", [])
        if isinstance(required_fields, list):
            missing = [field for field in required_fields if field not in arguments]
            if missing:
                raise ToolValidationError(
                    tool_name,
                    reason=f"Missing required parameter(s): {', '.join(missing)}",
                )
