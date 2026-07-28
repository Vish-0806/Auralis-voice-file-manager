"""Clarification Session Manager for managing clarification request lifecycles."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from brain.execution.clarification_engine import (
    ClarificationEngine,
    ClarificationRequest,
    ClarificationResponse,
    ClarificationContext,
)
from brain.execution.execution_state import ExecutionStatus
from brain.execution.execution_state_manager import ExecutionStateManager


class ClarificationSessionStatus(str, Enum):
    """Lifecycle status stages of a clarification session."""

    PENDING = "PENDING"
    RESPONDED = "RESPONDED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class ClarificationSession(BaseModel):
    """Domain model tracking an active clarification session."""

    session_id: str = Field(description="Unique identifier for the clarification session")
    execution_id: str = Field(description="Associated execution identifier")
    clarification_request: ClarificationRequest = Field(description="The underlying clarification request payload")
    status: ClarificationSessionStatus = Field(
        default=ClarificationSessionStatus.PENDING,
        description="Current session lifecycle status",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last status update timestamp",
    )
    expires_at: datetime = Field(description="Expiration timestamp when request times out")
    response: Optional[ClarificationResponse] = Field(
        default=None,
        description="User submitted response payload",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom session metadata dictionary",
    )

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Determines whether the session has exceeded its expiration timestamp.

        Args:
            now: Optional current timestamp override.

        Returns:
            True if current time > expires_at, False otherwise.
        """
        current_time = now or datetime.now(timezone.utc)
        return current_time > self.expires_at


class ClarificationSessionConfig(BaseModel):
    """Configuration parameters for the ClarificationSessionManager."""

    default_timeout_seconds: int = Field(
        default=300,
        ge=1,
        description="Default timeout in seconds for new clarification sessions",
    )
    cleanup_interval_seconds: int = Field(
        default=60,
        ge=1,
        description="Recommended interval in seconds for running expiration cleanup",
    )
    maximum_active_sessions: int = Field(
        default=500,
        ge=1,
        description="Maximum active/pending clarification sessions allowed in memory",
    )


class ClarificationSessionManager:
    """Manages the complete lifecycle of clarification sessions thread-safely."""

    def __init__(
        self,
        config: Optional[ClarificationSessionConfig] = None,
        engine: Optional[ClarificationEngine] = None,
        state_manager: Optional[ExecutionStateManager] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initializes the session manager with dependencies and thread lock.

        Args:
            config: Optional session configuration options.
            engine: Optional ClarificationEngine instance for response validation and application.
            state_manager: Optional ExecutionStateManager for tracking execution state.
            logger: Optional custom logger for session events.
        """
        self._config = config or ClarificationSessionConfig()
        self._engine = engine or ClarificationEngine()
        self._state_manager = state_manager
        self._logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._active_sessions: Dict[str, ClarificationSession] = {}

    def create_session(
        self,
        execution_id: str,
        clarification_request: ClarificationRequest,
        timeout_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ClarificationSession]:
        """Creates a new pending clarification session for an execution.

        Args:
            execution_id: Unique identifier of the execution requiring clarification.
            clarification_request: Structured clarification request payload.
            timeout_seconds: Optional explicit session timeout in seconds.
            metadata: Optional additional context metadata.

        Returns:
            Created ClarificationSession object, or None if inputs are invalid.
        """
        if not execution_id or not clarification_request:
            return None

        with self._lock:
            # Clean up expired sessions if capacity limits are reached
            if len(self._active_sessions) >= self._config.maximum_active_sessions:
                self.expire_sessions()

            timeout = timeout_seconds
            if timeout is None:
                timeout = getattr(clarification_request, "timeout_seconds", None)
            if timeout is None or timeout <= 0:
                timeout = self._config.default_timeout_seconds

            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=timeout)
            session_id = f"session_{uuid.uuid4().hex[:12]}"

            session = ClarificationSession(
                session_id=session_id,
                execution_id=execution_id,
                clarification_request=clarification_request,
                status=ClarificationSessionStatus.PENDING,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
                metadata=metadata or {},
            )

            self._active_sessions[session_id] = session

            if self._state_manager:
                state = self._state_manager.get_execution(execution_id)
                if state:
                    state.waiting_for_confirmation = True
                    state.clarification_request_id = session_id
                    state.clarification_reason = clarification_request.question
                    state.status = ExecutionStatus.WAITING_FOR_CONFIRMATION
                    state.updated_at = now

            self._logger.info(
                "Clarification Session Created",
                extra={"session_id": session_id, "execution_id": execution_id},
            )

            return session

    def get_session(self, session_id: str) -> Optional[ClarificationSession]:
        """Retrieves a clarification session by ID.

        Args:
            session_id: Unique session identifier.

        Returns:
            ClarificationSession instance or None if not found. Never raises exceptions.
        """
        if not session_id or not isinstance(session_id, str):
            return None
        with self._lock:
            return self._active_sessions.get(session_id)

    def list_pending(self) -> List[ClarificationSession]:
        """Lists all pending active clarification sessions.

        Returns:
            List of ClarificationSession objects currently in PENDING state.
        """
        with self._lock:
            return [
                s for s in self._active_sessions.values()
                if s.status == ClarificationSessionStatus.PENDING
            ]

    def submit_response(
        self,
        session_id: str,
        clarification_response: ClarificationResponse,
    ) -> bool:
        """Validates and submits a user response to a pending clarification session.

        Args:
            session_id: Target session identifier.
            clarification_response: Response payload submitted by user.

        Returns:
            True if response is valid and submitted, False otherwise.
        """
        if not session_id or not clarification_response:
            return False

        with self._lock:
            session = self._active_sessions.get(session_id)
            if not session or session.status != ClarificationSessionStatus.PENDING:
                return False

            now = datetime.now(timezone.utc)
            if now > session.expires_at:
                session.status = ClarificationSessionStatus.TIMED_OUT
                session.updated_at = now
                self._logger.info(
                    "Clarification Session Timed Out",
                    extra={"session_id": session_id, "execution_id": session.execution_id},
                )
                return False

            if not self._engine.validate_response(session.clarification_request, clarification_response):
                return False

            session.status = ClarificationSessionStatus.RESPONDED
            session.response = clarification_response
            session.updated_at = now

            self._logger.info(
                "Clarification Response Received",
                extra={"session_id": session_id, "execution_id": session.execution_id},
            )

            return True

    def resume_execution(self, session_id: str) -> Optional[ClarificationContext]:
        """Prepares an execution for resumption after a valid response is recorded.

        Args:
            session_id: Target session identifier.

        Returns:
            Updated ClarificationContext with applied responses, or None if invalid.
        """
        if not session_id or not isinstance(session_id, str):
            return None

        with self._lock:
            session = self._active_sessions.get(session_id)
            if not session or not session.response:
                return None
            if session.status not in (ClarificationSessionStatus.RESPONDED, ClarificationSessionStatus.PENDING):
                return None

            # Create context and apply user response resolution
            context = ClarificationContext(metadata=dict(session.metadata))
            self._engine.apply_response(context, session.response)

            # Update ExecutionState
            now = datetime.now(timezone.utc)
            if self._state_manager:
                state = self._state_manager.get_execution(session.execution_id)
                if state:
                    state.waiting_for_confirmation = False
                    state.clarification_request_id = None
                    if state.status == ExecutionStatus.WAITING_FOR_CONFIRMATION:
                        state.status = ExecutionStatus.RUNNING
                    if session.response and session.response.selected_choice:
                        state.metadata["resolved_choice"] = session.response.selected_choice
                        state.metadata["confirmed"] = session.response.confirmed
                    state.updated_at = now

            session.status = ClarificationSessionStatus.COMPLETED
            session.updated_at = now

            self._logger.info(
                "Execution Ready To Resume",
                extra={"session_id": session_id, "execution_id": session.execution_id},
            )

            return context

    def expire_sessions(self) -> List[str]:
        """Scans active sessions and marks any expired sessions as TIMED_OUT.

        Returns:
            List of session IDs that timed out during this check.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            timed_out_ids: List[str] = []

            for session in list(self._active_sessions.values()):
                if session.status == ClarificationSessionStatus.PENDING and now > session.expires_at:
                    session.status = ClarificationSessionStatus.TIMED_OUT
                    session.updated_at = now
                    timed_out_ids.append(session.session_id)

                    if self._state_manager:
                        state = self._state_manager.get_execution(session.execution_id)
                        if state:
                            state.waiting_for_confirmation = False
                            state.metadata["clarification_timeout"] = True
                            state.updated_at = now

                    self._logger.info(
                        "Clarification Session Timed Out",
                        extra={"session_id": session.session_id, "execution_id": session.execution_id},
                    )

            return timed_out_ids

    def cancel_session(self, session_id: str) -> bool:
        """Cancels a pending or active clarification session.

        Args:
            session_id: Target session identifier.

        Returns:
            True if session was cancelled, False if unknown or already finalized.
        """
        if not session_id or not isinstance(session_id, str):
            return False

        with self._lock:
            session = self._active_sessions.get(session_id)
            if not session:
                return False
            if session.status in (ClarificationSessionStatus.COMPLETED, ClarificationSessionStatus.CANCELLED):
                return False

            now = datetime.now(timezone.utc)
            session.status = ClarificationSessionStatus.CANCELLED
            session.updated_at = now

            if self._state_manager:
                state = self._state_manager.get_execution(session.execution_id)
                if state:
                    state.waiting_for_confirmation = False
                    state.status = ExecutionStatus.CANCELLED
                    state.updated_at = now

            self._logger.info(
                "Clarification Session Cancelled",
                extra={"session_id": session_id, "execution_id": session.execution_id},
            )

            return True

    def remove_session(self, session_id: str) -> bool:
        """Removes a session from memory.

        Args:
            session_id: Target session identifier.

        Returns:
            True if session was removed, False if not found.
        """
        if not session_id or not isinstance(session_id, str):
            return False

        with self._lock:
            if session_id in self._active_sessions:
                session = self._active_sessions.pop(session_id)
                self._logger.info(
                    "Clarification Session Removed",
                    extra={"session_id": session_id, "execution_id": session.execution_id},
                )
                return True
            return False

    def clear(self) -> None:
        """Clears all tracked clarification sessions from memory."""
        with self._lock:
            self._active_sessions.clear()
