"""Feedback Generator for the Auralis Voice Orchestration Engine (Phase 9.6).

Produces deterministic, template-based spoken feedback.
No randomness. No LLM. No filesystem interaction. Stateless.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from brain.voice.voice_models import (
    VoiceCommand,
    VoiceFeedback,
    VoiceInteractionResult,
    VoiceCommandStatus,
)

logger = logging.getLogger(__name__)


class FeedbackGenerator:
    """Stateless, deterministic spoken-feedback generator.

    All output is produced from fixed templates keyed on command state,
    operation type, and success/failure outcome. No randomness, no
    LLM calls, no external I/O.
    """

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def generate(
        self,
        command: VoiceCommand,
        result: VoiceInteractionResult,
    ) -> VoiceFeedback:
        """Generate feedback for a completed voice interaction.

        Args:
            command: The original voice command.
            result: The final interaction result.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        if result.success:
            text = self._success_text(command)
        else:
            text = self._failure_text(command, result.error)

        feedback = self._make_feedback(command, text, success=result.success,
                                       duration_ms=result.pipeline_ms)
        logger.info(
            "Voice Feedback Generated: session_id=%s command_id=%s success=%s",
            command.session_id, command.command_id, result.success,
        )
        return feedback

    def generate_started(self, command: VoiceCommand) -> VoiceFeedback:
        """Feedback indicating a command has started processing.

        Args:
            command: The voice command that started.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        normalized = command.normalized_text.strip() or command.raw_text.strip()
        text = f"Processing: {normalized}." if normalized else "Processing your request."
        return self._make_feedback(command, text, success=True)

    def generate_cancelled(self, command: VoiceCommand) -> VoiceFeedback:
        """Feedback indicating a command was cancelled.

        Args:
            command: The cancelled voice command.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        return self._make_feedback(command, "Operation cancelled.", success=False)

    def generate_confirmation_request(
        self,
        prompt: str,
        command: Optional[VoiceCommand] = None,
    ) -> VoiceFeedback:
        """Feedback presenting a confirmation prompt to the user.

        Args:
            prompt: The confirmation question.
            command: Optional source command.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        dummy = command or VoiceCommand()
        text = prompt if prompt else "Please confirm the operation."
        return self._make_feedback(dummy, text, success=True)

    def generate_clarification_request(
        self,
        prompt: str,
        options: Optional[list] = None,
        command: Optional[VoiceCommand] = None,
    ) -> VoiceFeedback:
        """Feedback presenting a clarification prompt to the user.

        Args:
            prompt: The clarification question.
            options: List of option strings (appended to prompt if short).
            command: Optional source command.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        dummy = command or VoiceCommand()
        if options and len(options) <= 5:
            opts_text = ", ".join(options)
            text = f"{prompt} Options: {opts_text}."
        else:
            text = prompt
        return self._make_feedback(dummy, text, success=True)

    def generate_error(
        self,
        command: VoiceCommand,
        error: Optional[str] = None,
    ) -> VoiceFeedback:
        """Feedback for an unexpected error.

        Args:
            command: Source command.
            error: Optional error message.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        text = self._failure_text(command, error)
        return self._make_feedback(command, text, success=False)

    def generate_permission_denied(self, command: VoiceCommand) -> VoiceFeedback:
        """Feedback for a permission-denied outcome.

        Args:
            command: Source command.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        return self._make_feedback(
            command,
            "Permission denied. I don't have access to perform that operation.",
            success=False,
        )

    def generate_session_ended(self, session_id: str) -> VoiceFeedback:
        """Feedback for a session that has ended.

        Args:
            session_id: Ended session ID.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        dummy = VoiceCommand(session_id=session_id)
        return self._make_feedback(dummy, "Session ended. Goodbye.", success=True)

    def generate_confirmation_accepted(self, command: VoiceCommand) -> VoiceFeedback:
        """Feedback when user accepts a confirmation.

        Args:
            command: Source command.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        return self._make_feedback(command, "Confirmed. Proceeding.", success=True)

    def generate_confirmation_rejected(self, command: VoiceCommand) -> VoiceFeedback:
        """Feedback when user rejects a confirmation.

        Args:
            command: Source command.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        return self._make_feedback(command, "Understood. Operation cancelled.", success=False)

    def generate_timeout(self, command: VoiceCommand) -> VoiceFeedback:
        """Feedback for a timed-out confirmation or clarification.

        Args:
            command: Source command.

        Returns:
            Immutable :class:`VoiceFeedback`.
        """
        return self._make_feedback(
            command,
            "No response received. Operation cancelled due to timeout.",
            success=False,
        )

    # ------------------------------------------------------------------
    # Internal Template Logic
    # ------------------------------------------------------------------

    def _success_text(self, command: VoiceCommand) -> str:
        """Build a success message from the command context."""
        normalized = command.normalized_text.strip() or command.raw_text.strip()
        if not normalized:
            return "Execution completed successfully."

        lower = normalized.lower()

        if lower.startswith("copy"):
            return "Copy completed successfully."
        if lower.startswith("move"):
            return "Move completed successfully."
        if lower.startswith("delete") or lower.startswith("remove"):
            return "Deletion completed successfully."
        if lower.startswith("create") or lower.startswith("make"):
            return "Created successfully."
        if lower.startswith("rename"):
            return "Renamed successfully."
        if lower.startswith("search") or lower.startswith("find"):
            return "Search completed."
        if lower.startswith("open"):
            return "Opened successfully."
        if lower.startswith("list"):
            return "Listing complete."

        return "Execution completed successfully."

    def _failure_text(self, command: VoiceCommand, error: Optional[str]) -> str:
        """Build a failure message from the command context and error."""
        if error:
            if "permission" in error.lower():
                return "Permission denied. I don't have access to perform that operation."
            if "not found" in error.lower() or "does not exist" in error.lower():
                return "The requested file or folder was not found."
            if "timeout" in error.lower():
                return "The operation timed out. Please try again."
            if "cancelled" in error.lower():
                return "Operation cancelled."
        return "Something went wrong. The operation could not be completed."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_feedback(
        self,
        command: VoiceCommand,
        text: str,
        success: bool,
        duration_ms: float = 0.0,
    ) -> VoiceFeedback:
        return VoiceFeedback(
            feedback_id=f"fb-{uuid.uuid4().hex[:8]}",
            command_id=command.command_id,
            session_id=command.session_id,
            text=text,
            success=success,
            duration_ms=duration_ms,
            created_at=datetime.now(timezone.utc),
        )
