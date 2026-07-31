"""Tool Calling Runtime package for Auralis (Phase 10.4).

Exports all tool metadata, permission levels, exceptions, interfaces, registries, parsers, and executors.
"""

from brain.ai.tools.exceptions import (
    ToolException,
    ToolExecutionError,
    ToolNotFoundError,
    ToolParsingError,
    ToolRegistrationError,
    ToolValidationError,
)
from brain.ai.tools.permissions import ToolPermissionLevel
from brain.ai.tools.metadata import ToolMetadata
from brain.ai.tools.interfaces import (
    AITool,
    ToolExecutorInterface,
    ToolParserInterface,
    ToolRegistryInterface,
)
from brain.ai.tools.registry import DefaultToolRegistry
from brain.ai.tools.parser import DefaultToolParser
from brain.ai.tools.executor import DefaultToolExecutor

__all__ = [
    # Exceptions
    "ToolException",
    "ToolNotFoundError",
    "ToolRegistrationError",
    "ToolValidationError",
    "ToolExecutionError",
    "ToolParsingError",
    # Permissions & Metadata
    "ToolPermissionLevel",
    "ToolMetadata",
    # Interfaces
    "AITool",
    "ToolRegistryInterface",
    "ToolParserInterface",
    "ToolExecutorInterface",
    # Concrete Runtime Implementations
    "DefaultToolRegistry",
    "DefaultToolParser",
    "DefaultToolExecutor",
]
