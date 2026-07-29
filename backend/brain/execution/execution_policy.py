"""Execution Policy configuration for the Auralis Execution Engine.

This module provides configurable rules governing retries, timeouts, error continuation,
rollbacks, and safe execution settings.
"""

from typing import Any, Dict
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ExecutionPolicy(BaseModel):
    """Configurable execution policy rules."""

    maximum_retries: int = Field(default=3, ge=0, description="Maximum number of retries per step")
    maximum_timeout_seconds: float = Field(default=300.0, gt=0.0, description="Overall execution plan timeout limit")
    step_timeout_seconds: float = Field(default=60.0, gt=0.0, description="Single step execution timeout limit")
    continue_on_warning: bool = Field(default=True, description="Whether to continue execution if warnings occur")
    continue_on_error: bool = Field(default=False, description="Whether to continue execution if non-critical errors occur")
    rollback_enabled: bool = Field(default=True, description="Whether to attempt step rollback upon failure")
    confirmation_required: bool = Field(default=False, description="Whether explicit user confirmation is required")
    safe_execution: bool = Field(default=True, description="Enforces strict safe execution mode")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional policy configuration metadata")
