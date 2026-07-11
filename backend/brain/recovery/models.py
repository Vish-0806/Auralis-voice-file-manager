"""Data models for Auralis Self-Correction and Recovery."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from core.models import ExecutionPlan as CoreExecutionPlan


class FailureType(str, Enum):
    """Supported execution failure types detected by the analyzer."""

    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class FallbackOption(BaseModel):
    """Represents a registered fallback choice for a failed component.

    Attributes:
        original: Name/target of the original component.
        fallback: Name/target of the fallback component.
        requires_confirmation: Whether user confirmation is required.
    """

    original: str = Field(description="Original target resource or application")
    fallback: str = Field(description="Fallback target resource or application")
    requires_confirmation: bool = Field(default=False, description="Whether confirmation is required before applying")


class RecoveryStrategy(BaseModel):
    """Defines a recovery path for a specific failure type.

    Attributes:
        failure_type: The FailureType handled by this strategy.
        name: Name of the recovery strategy.
        description: Informative description.
        remediation_actions: Core plans to execute for recovery.
    """

    failure_type: FailureType = Field(description="The failure type handled")
    name: str = Field(description="Name of the recovery strategy")
    description: str = Field(description="Description of how recovery is achieved")
    remediation_actions: List[CoreExecutionPlan] = Field(default_factory=list, description="Remediation steps")


class RecoveryResult(BaseModel):
    """Summary of a recovery attempt.

    Attributes:
        success: Whether recovery was successfully resolved.
        strategy_applied: Optional name of the recovery strategy applied.
        remediation_actions: Action plans executed to recover.
        error: Error details if recovery failed.
    """

    success: bool = Field(description="Whether recovery was successful")
    strategy_applied: Optional[str] = Field(None, description="The name of the strategy applied")
    remediation_actions: List[CoreExecutionPlan] = Field(default_factory=list, description="Remediation steps executed")
    error: Optional[str] = Field(None, description="Error message if recovery failed")
