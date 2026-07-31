"""Immutable Tool Metadata definition for Auralis (Phase 10.4).

Defines ToolMetadata Pydantic model.
"""

from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.ai.ai_models import ToolCategory
from brain.ai.tools.permissions import ToolPermissionLevel


class ToolMetadata(BaseModel):
    """Immutable metadata describing an AI Tool schema, category, and permission requirements."""

    model_config = ConfigDict(frozen=True)

    tool_name: str
    description: str
    category: ToolCategory = ToolCategory.FILESYSTEM
    parameters: Dict[str, Any] = Field(default_factory=dict)
    return_schema: Optional[Dict[str, Any]] = None
    permission_level: ToolPermissionLevel = ToolPermissionLevel.READ
    enabled: bool = True
