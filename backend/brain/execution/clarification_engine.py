"""Interactive Clarification Engine for detecting and prompting on ambiguous execution plans."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from core.intents import Intent


class ClarificationType(str, Enum):
    """Enumeration of standard interactive clarification scenarios."""

    MISSING_TARGET = "MISSING_TARGET"
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    AMBIGUOUS_INTENT = "AMBIGUOUS_INTENT"
    CONFIRMATION = "CONFIRMATION"
    WORKSPACE_SELECTION = "WORKSPACE_SELECTION"
    APPLICATION_SELECTION = "APPLICATION_SELECTION"
    FILE_SELECTION = "FILE_SELECTION"
    UNKNOWN = "UNKNOWN"


class ClarificationChoice(BaseModel):
    """A single choice option presented inside a clarification prompt."""

    id: str = Field(description="Unique choice identifier")
    label: str = Field(description="Human readable selection label")
    description: Optional[str] = Field(default=None, description="Optional detail describing the selection choice")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags attached to the selection")


class ClarificationRequest(BaseModel):
    """Prompts the caller for clarification to resolve plan ambiguities."""

    clarification_id: str = Field(description="Unique identifier for the clarification request")
    type: ClarificationType = Field(description="Scenario category of the clarification request")
    question: str = Field(description="Detailed user facing clarification question prompt")
    choices: List[ClarificationChoice] = Field(description="List of choices presented to the user")
    default_choice: Optional[str] = Field(default=None, description="Identifier of the fallback option selection")
    required: bool = Field(default=True, description="Whether a valid option must be selected before resuming")
    timeout_seconds: int = Field(default=60, description="Expiration time limit in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or custom metadata")


class ClarificationResponse(BaseModel):
    """Stores user's resolution selection response to a ClarificationRequest."""

    clarification_id: str = Field(description="Reference ID matching request clarification_id")
    selected_choice: Optional[str] = Field(default=None, description="Selected choice ID, if applicable")
    confirmed: bool = Field(default=False, description="Explicit confirmation response selection")
    timestamp: float = Field(description="Timestamp in seconds when user response was gathered")


class ClarificationContext(BaseModel):
    """Context block evaluated by ClarificationEngine to check for plan ambiguities."""

    assistant_context: Optional[Dict[str, Any]] = Field(default=None, description="Active assistant context details")
    execution_plan: Optional[Any] = Field(default=None, description="Referenced routed execution plan, if available")
    execution_step: Optional[Any] = Field(default=None, description="Referenced single execution step plan")
    workspace_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Workspace structure metadata")
    resolved_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Learned developer environment settings")
    decision: Optional[Any] = Field(default=None, description="DecisionEngine execution decisions context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags dictionary")


class ClarificationEngine:
    """Detects ambiguity within execution requests and builds structured choices."""

    def detect_clarification(self, context: ClarificationContext) -> bool:
        """Determines if the current plan context matches any ambiguity rules.

        Args:
            context: The context variables representing active workspace and execution state.

        Returns:
            True if clarification is required, False otherwise.
        """
        if not context:
            return False

        step = context.execution_step
        plan = context.execution_plan
        target = step.target if step else (plan.target if plan else None)
        intent = step.intent if step else (plan.intent if plan else None)

        # Rule 1: MISSING_TARGET
        if not target and intent:
            return True

        # Rule 2: WORKSPACE_SELECTION (Multiple projects)
        if target == "project" and context.workspace_analysis and len(context.workspace_analysis.get("projects", [])) > 1:
            return True
        if context.metadata.get("multiple_projects") or (context.workspace_analysis and context.workspace_analysis.get("multiple_projects")):
            return True

        # Rule 3: APPLICATION_SELECTION (Multiple browsers/editors)
        if target == "browser" and context.resolved_preferences and len(context.resolved_preferences.get("browsers", [])) > 1:
            return True
        if context.metadata.get("multiple_applications") or (context.resolved_preferences and context.resolved_preferences.get("multiple_applications")):
            return True

        # Rule 4: FILE_SELECTION (Multiple files matching wildcard or names)
        if target == "file" and context.workspace_analysis and len(context.workspace_analysis.get("matched_files", [])) > 1:
            return True
        if context.metadata.get("multiple_files") or (context.workspace_analysis and context.workspace_analysis.get("multiple_files")):
            return True

        # Rule 5: CONFIRMATION (High-risk operations)
        if target == "Downloads" or context.metadata.get("needs_confirmation") or (step and step.parameters and step.parameters.get("confirm_required")):
            return True

        # Rule 6: MISSING_PARAMETER (No destination parameter)
        if step and step.parameters and "destination" in step.parameters and step.parameters["destination"] is None:
            return True
        if context.metadata.get("missing_parameter"):
            return True

        # Rule 7: AMBIGUOUS_INTENT
        if context.metadata.get("ambiguous_intent") or intent == Intent.UNKNOWN or str(intent) == "UNKNOWN" or "UNKNOWN" in str(intent):
            return True

        return False

    def generate_request(self, context: ClarificationContext) -> Optional[ClarificationRequest]:
        """Creates a structured ClarificationRequest containing prompt details and options.

        Args:
            context: The context variables representing active workspace and execution state.

        Returns:
            A structured ClarificationRequest, or None if no ambiguity is detected.
        """
        if not self.detect_clarification(context):
            return None

        step = context.execution_step
        plan = context.execution_plan
        target = step.target if step else (plan.target if plan else None)
        intent = step.intent if step else (plan.intent if plan else None)

        clarification_id = context.metadata.get("clarification_id") or "clar_req_1"
        timeout_seconds = context.metadata.get("timeout_seconds") or 60

        # Case 1: MISSING_TARGET
        if not target and intent:
            return ClarificationRequest(
                clarification_id=clarification_id,
                type=ClarificationType.MISSING_TARGET,
                question="Please specify the target for this execution action.",
                choices=[
                    ClarificationChoice(id="file", label="File", description="Target a specific file"),
                    ClarificationChoice(id="folder", label="Folder", description="Target a folder path"),
                ],
                default_choice="file",
                required=True,
                timeout_seconds=timeout_seconds,
            )

        # Case 2: WORKSPACE_SELECTION
        if (target == "project" and context.workspace_analysis and len(context.workspace_analysis.get("projects", [])) > 1) or context.metadata.get("multiple_projects"):
            projects = (context.workspace_analysis or {}).get("projects") or ["Project A", "Project B"]
            choices = [ClarificationChoice(id=p.lower().replace(" ", "_"), label=p, description=f"Workspace project named {p}") for p in projects]
            return ClarificationRequest(
                clarification_id=clarification_id,
                type=ClarificationType.WORKSPACE_SELECTION,
                question="Multiple projects found. Which project would you like to target?",
                choices=choices,
                default_choice=choices[0].id if choices else None,
                required=True,
                timeout_seconds=timeout_seconds,
            )

        # Case 3: APPLICATION_SELECTION
        if (target == "browser" and context.resolved_preferences and len(context.resolved_preferences.get("browsers", [])) > 1) or context.metadata.get("multiple_applications"):
            browsers = (context.resolved_preferences or {}).get("browsers") or ["Chrome", "Firefox"]
            choices = [ClarificationChoice(id=b.lower(), label=b, description=f"Use the {b} browser application") for b in browsers]
            return ClarificationRequest(
                clarification_id=clarification_id,
                type=ClarificationType.APPLICATION_SELECTION,
                question="Multiple browsers installed. Which application would you like to use?",
                choices=choices,
                default_choice=choices[0].id if choices else None,
                required=True,
                timeout_seconds=timeout_seconds,
            )

        # Case 4: FILE_SELECTION
        if (target == "file" and context.workspace_analysis and len(context.workspace_analysis.get("matched_files", [])) > 1) or context.metadata.get("multiple_files"):
            files = (context.workspace_analysis or {}).get("matched_files") or ["notes.txt", "notes.md"]
            choices = [ClarificationChoice(id=f, label=f, description=f"File path: {f}") for f in files]
            return ClarificationRequest(
                clarification_id=clarification_id,
                type=ClarificationType.FILE_SELECTION,
                question="Multiple files match. Which file would you like to select?",
                choices=choices,
                default_choice=choices[0].id if choices else None,
                required=True,
                timeout_seconds=timeout_seconds,
            )

        # Case 5: CONFIRMATION
        if target == "Downloads" or context.metadata.get("needs_confirmation") or (step and step.parameters and step.parameters.get("confirm_required")):
            return ClarificationRequest(
                clarification_id=clarification_id,
                type=ClarificationType.CONFIRMATION,
                question=f"Are you sure you want to proceed with this operation on {target or 'Downloads'}?",
                choices=[
                    ClarificationChoice(id="yes", label="Yes", description="Proceed with execution"),
                    ClarificationChoice(id="no", label="No", description="Cancel execution"),
                ],
                default_choice="no",
                required=True,
                timeout_seconds=timeout_seconds,
            )

        # Case 6: MISSING_PARAMETER
        if (step and step.parameters and "destination" in step.parameters and step.parameters["destination"] is None) or context.metadata.get("missing_parameter"):
            return ClarificationRequest(
                clarification_id=clarification_id,
                type=ClarificationType.MISSING_PARAMETER,
                question="A required execution parameter is missing. Please provide the destination path.",
                choices=[
                    ClarificationChoice(id="dest_a", label="/dest/a", description="Destination path A"),
                    ClarificationChoice(id="dest_b", label="/dest/b", description="Destination path B"),
                ],
                default_choice="dest_a",
                required=True,
                timeout_seconds=timeout_seconds,
            )

        # Case 7: AMBIGUOUS_INTENT / general fallback
        return ClarificationRequest(
            clarification_id=clarification_id,
            type=ClarificationType.AMBIGUOUS_INTENT,
            question="The action intent is ambiguous. Please select an option to clarify.",
            choices=[
                ClarificationChoice(id="intent_a", label="Option A", description="Perform Option A"),
                ClarificationChoice(id="intent_b", label="Option B", description="Perform Option B"),
            ],
            default_choice="intent_a",
            required=True,
            timeout_seconds=timeout_seconds,
        )

    def validate_response(self, request: ClarificationRequest, response: ClarificationResponse) -> bool:
        """Validates that the given response corresponds to the request options.

        Args:
            request: The generated request prompt payload.
            response: The response submitted by the user.

        Returns:
            True if response matches validation criteria, False otherwise.
        """
        if not request or not response:
            return False
        if request.clarification_id != response.clarification_id:
            return False
        if request.required and response.selected_choice is None and not response.confirmed:
            return False
        if response.selected_choice:
            valid_ids = {c.id for c in request.choices}
            if response.selected_choice not in valid_ids:
                return False
        return True

    def apply_response(self, context: ClarificationContext, response: ClarificationResponse) -> None:
        """Merges the response resolution back into context metadata.

        Args:
            context: The target context parameters of execution.
            response: The valid response submitted by the user.
        """
        if not context or not response:
            return
        if not context.metadata:
            context.metadata = {}
        context.metadata["resolved_choice"] = response.selected_choice
        context.metadata["confirmed"] = response.confirmed
        context.metadata["resolved_timestamp"] = response.timestamp
