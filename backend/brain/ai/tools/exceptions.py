"""Tool Calling Runtime Exception Hierarchy for Auralis (Phase 10.4).

Defines exception types for tool registration, parsing, validation, execution, and lookup.
"""

from brain.ai.exceptions import AIException


class ToolException(AIException):
    """Base exception for all tool calling runtime errors in Auralis."""

    pass


class ToolNotFoundError(ToolException):
    """Raised when a requested tool is not registered in the ToolRegistry."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' is not registered in ToolRegistry.")


class ToolRegistrationError(ToolException):
    """Raised when registering an invalid or duplicate tool."""

    pass


class ToolValidationError(ToolException):
    """Raised when tool arguments fail schema validation."""

    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Validation failed for tool '{tool_name}': {reason}")


class ToolExecutionError(ToolException):
    """Raised when a tool encounters an error during execution."""

    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Execution failed for tool '{tool_name}': {reason}")


class ToolParsingError(ToolException):
    """Raised when parsing raw provider tool call payload fails."""

    pass
