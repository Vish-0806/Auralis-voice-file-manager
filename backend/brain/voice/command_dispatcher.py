"""Command Dispatcher for the Auralis Voice Orchestration Engine (Phase 9.6).

Receives validated voice commands, dispatches them into the Conversation Engine,
and maps the resulting ExecutionResult into a VoiceInteractionResult.

Does NOT perform reasoning, planning, filesystem operations, or speech synthesis.
"""

import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from brain.voice.voice_models import (
    VoiceCommand,
    VoiceCommandStatus,
    VoiceFeedback,
    VoiceInteractionResult,
)

logger = logging.getLogger(__name__)

# Type alias for the pipeline callable injected by tests or the runtime
PipelineCallable = Callable[[str, str, Dict[str, Any]], Dict[str, Any]]


class CommandDispatcher:
    """Thread-safe dispatcher that sends voice commands into the Brain Pipeline.

    The dispatcher uses an injectable ``pipeline`` callable so the class
    remains decoupled from the concrete Conversation Engine implementation.

    In production the ``pipeline`` will call
    ``ConversationRuntimeCoordinator.get_coordinator().process(...)`` or
    an equivalent entry-point.  In tests a lightweight stub is injected.
    """

    def __init__(
        self,
        pipeline: Optional[PipelineCallable] = None,
    ) -> None:
        """Initialises CommandDispatcher.

        Args:
            pipeline: Optional callable ``(text, session_id, metadata) → dict``.
                      Defaults to a no-op stub if not provided.
        """
        self._lock = threading.RLock()
        self._pipeline: PipelineCallable = pipeline or _noop_pipeline
        self._dispatch_log: List[Dict[str, Any]] = []
        logger.debug("CommandDispatcher initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dispatch(
        self,
        command: VoiceCommand,
        conversation_id: Optional[str] = None,
    ) -> VoiceInteractionResult:
        """Dispatch *command* through the Brain Pipeline.

        Args:
            command: Validated voice command to dispatch.
            conversation_id: Optional conversation ID for the brain pipeline.

        Returns:
            Immutable :class:`VoiceInteractionResult`.
        """
        dispatch_id = f"disp-{uuid.uuid4().hex[:8]}"
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()

        logger.info(
            "Command Dispatched: command_id=%s session_id=%s dispatch_id=%s",
            command.command_id, command.session_id, dispatch_id,
        )

        try:
            metadata: Dict[str, Any] = {
                "command_id": command.command_id,
                "session_id": command.session_id,
                "dispatch_id": dispatch_id,
                "language": command.language,
                "confidence": command.confidence,
                **command.metadata,
            }
            if conversation_id:
                metadata["conversation_id"] = conversation_id

            raw_result = self._pipeline(
                command.normalized_text or command.raw_text,
                command.session_id,
                metadata,
            )

            pipeline_ms = (time.monotonic() - t0) * 1000
            success = bool(raw_result.get("success", True))
            error = raw_result.get("error") if not success else None

            result = VoiceInteractionResult(
                command_id=command.command_id,
                session_id=command.session_id,
                success=success,
                status=VoiceCommandStatus.COMPLETED if success else VoiceCommandStatus.FAILED,
                pipeline_ms=pipeline_ms,
                error=error,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                metadata={
                    "dispatch_id": dispatch_id,
                    "pipeline_output": raw_result,
                },
            )

            self._record_dispatch(command, result, dispatch_id)
            logger.info(
                "Execution Returned: command_id=%s success=%s pipeline_ms=%.1f",
                command.command_id, success, pipeline_ms,
            )
            return result

        except Exception as exc:
            pipeline_ms = (time.monotonic() - t0) * 1000
            error_msg = str(exc)
            logger.error(
                "CommandDispatcher.dispatch failed command_id=%s error=%s",
                command.command_id, error_msg,
            )
            result = VoiceInteractionResult(
                command_id=command.command_id,
                session_id=command.session_id,
                success=False,
                status=VoiceCommandStatus.FAILED,
                pipeline_ms=pipeline_ms,
                error=error_msg,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                metadata={"dispatch_id": dispatch_id},
            )
            self._record_dispatch(command, result, dispatch_id)
            return result

    def set_pipeline(self, pipeline: PipelineCallable) -> None:
        """Replace the pipeline callable (useful for testing or hot-swapping).

        Args:
            pipeline: New callable to use for dispatching.
        """
        with self._lock:
            self._pipeline = pipeline
            logger.debug("CommandDispatcher pipeline replaced")

    def get_dispatch_log(self) -> List[Dict[str, Any]]:
        """Return a copy of the internal dispatch log.

        Returns:
            List of dispatch record dicts.
        """
        with self._lock:
            return list(self._dispatch_log)

    def clear_log(self) -> None:
        """Clear the internal dispatch log."""
        with self._lock:
            self._dispatch_log.clear()

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _record_dispatch(
        self,
        command: VoiceCommand,
        result: VoiceInteractionResult,
        dispatch_id: str,
    ) -> None:
        with self._lock:
            self._dispatch_log.append({
                "dispatch_id": dispatch_id,
                "command_id": command.command_id,
                "session_id": command.session_id,
                "success": result.success,
                "pipeline_ms": result.pipeline_ms,
                "dispatched_at": result.started_at.isoformat(),
            })


# ---------------------------------------------------------------------------
# Default No-Op Pipeline
# ---------------------------------------------------------------------------

def _noop_pipeline(text: str, session_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Default no-op pipeline stub used when no real pipeline is injected."""
    return {"success": True, "text": text, "session_id": session_id}
