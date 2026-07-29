"""Clarification Manager for the Auralis Voice Orchestration Engine (Phase 9.6).

Manages the lifecycle of voice clarification workflows for ambiguous commands.
Thread-safe, deterministic. No LLM, no filesystem interaction.
"""

import logging
import threading
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from brain.voice.voice_models import ClarificationStatus, VoiceClarification

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS: float = 30.0


class ClarificationManager:
    """Thread-safe manager for voice clarification workflows.

    Responsibilities:
    - Issue clarification prompts when commands are ambiguous.
    - Accept user option selection and resolve the clarification.
    - Cancel or time out pending clarifications.
    - Build deterministic prompts from multiple match candidates.
    """

    def __init__(self, default_timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS) -> None:
        """Initialises ClarificationManager.

        Args:
            default_timeout_seconds: Default expiry window for clarifications.
        """
        self._lock = threading.RLock()
        self._default_timeout = default_timeout_seconds
        # clarification_id → VoiceClarification
        self._clarifications: Dict[str, VoiceClarification] = {}
        # session_id → [clarification_id, ...]
        self._session_index: Dict[str, List[str]] = {}
        logger.debug("ClarificationManager initialized timeout=%.1fs", default_timeout_seconds)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_clarification(
        self,
        session_id: str,
        prompt: str,
        options: List[str],
        command_id: str = "",
        timeout_seconds: Optional[float] = None,
    ) -> VoiceClarification:
        """Create and store a new pending clarification.

        Args:
            session_id: Session requesting clarification.
            prompt: Human-readable clarification question.
            options: List of option strings the user can choose from.
            command_id: Associated command ID.
            timeout_seconds: Override default timeout.

        Returns:
            Immutable :class:`VoiceClarification` in PENDING state.
        """
        with self._lock:
            clar_id = f"clar-{uuid.uuid4().hex[:8]}"
            timeout = timeout_seconds if timeout_seconds is not None else self._default_timeout
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=timeout)

            clarification = VoiceClarification(
                clarification_id=clar_id,
                session_id=session_id,
                command_id=command_id,
                prompt=prompt,
                options=list(options),
                status=ClarificationStatus.PENDING,
                timeout_seconds=timeout,
                created_at=now,
                expires_at=expires_at,
            )
            self._clarifications[clar_id] = clarification
            self._session_index.setdefault(session_id, []).append(clar_id)
            logger.info(
                "Clarification Requested: session_id=%s clarification_id=%s options=%d",
                session_id, clar_id, len(options),
            )
            return clarification

    def receive_response(
        self,
        clarification_id: str,
        selected_option: str,
    ) -> VoiceClarification:
        """Record the user's option selection and resolve the clarification.

        Args:
            clarification_id: Clarification being answered.
            selected_option: The option selected by the user.

        Returns:
            Updated immutable :class:`VoiceClarification`.
        """
        with self._lock:
            clar = self._clarifications.get(clarification_id)
            if clar is None:
                logger.warning("ClarificationManager.receive_response: unknown id=%s", clarification_id)
                return VoiceClarification(
                    clarification_id=clarification_id,
                    status=ClarificationStatus.RECEIVED,
                    selected_option=selected_option,
                    metadata={"error": "not_found"},
                )

            if clar.status != ClarificationStatus.PENDING:
                logger.warning(
                    "ClarificationManager.receive_response: already resolved id=%s status=%s",
                    clarification_id, clar.status,
                )
                return clar

            updated = clar.model_copy(update={
                "status": ClarificationStatus.RECEIVED,
                "selected_option": selected_option,
                "resolved_at": datetime.now(timezone.utc),
            })
            self._clarifications[clarification_id] = updated
            logger.info(
                "Clarification Received: clarification_id=%s selected=%s",
                clarification_id, selected_option,
            )
            return updated

    def cancel(self, clarification_id: str) -> VoiceClarification:
        """Mark a clarification as CANCELLED.

        Args:
            clarification_id: Clarification to cancel.

        Returns:
            Updated immutable :class:`VoiceClarification`.
        """
        with self._lock:
            clar = self._clarifications.get(clarification_id)
            if clar is None:
                logger.warning("ClarificationManager.cancel: unknown id=%s", clarification_id)
                return VoiceClarification(
                    clarification_id=clarification_id,
                    status=ClarificationStatus.CANCELLED,
                    metadata={"error": "not_found"},
                )

            if clar.status != ClarificationStatus.PENDING:
                return clar

            updated = clar.model_copy(update={
                "status": ClarificationStatus.CANCELLED,
                "resolved_at": datetime.now(timezone.utc),
            })
            self._clarifications[clarification_id] = updated
            logger.info("Clarification cancelled: clarification_id=%s", clarification_id)
            return updated

    def check_timeouts(self) -> List[VoiceClarification]:
        """Scan all PENDING clarifications and mark expired ones as TIMED_OUT.

        Returns:
            List of clarifications that were just timed out.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            timed_out: List[VoiceClarification] = []
            for clar_id, clar in list(self._clarifications.items()):
                if clar.status == ClarificationStatus.PENDING:
                    if clar.expires_at and now > clar.expires_at:
                        updated = clar.model_copy(update={
                            "status": ClarificationStatus.TIMED_OUT,
                            "resolved_at": now,
                        })
                        self._clarifications[clar_id] = updated
                        timed_out.append(updated)
                        logger.info(
                            "Clarification timed out: clarification_id=%s session_id=%s",
                            clar_id, clar.session_id,
                        )
            return timed_out

    def get_clarification(self, clarification_id: str) -> Optional[VoiceClarification]:
        """Return clarification by ID, checking timeout lazily.

        Args:
            clarification_id: ID to look up.

        Returns:
            :class:`VoiceClarification` or None.
        """
        with self._lock:
            clar = self._clarifications.get(clarification_id)
            if clar is None:
                return None
            if clar.status == ClarificationStatus.PENDING and clar.expires_at:
                if datetime.now(timezone.utc) > clar.expires_at:
                    clar = clar.model_copy(update={
                        "status": ClarificationStatus.TIMED_OUT,
                        "resolved_at": datetime.now(timezone.utc),
                    })
                    self._clarifications[clarification_id] = clar
            return clar

    def get_history(self, session_id: str) -> List[VoiceClarification]:
        """Return all clarifications for a session.

        Args:
            session_id: Session to look up.

        Returns:
            List of :class:`VoiceClarification` objects.
        """
        with self._lock:
            clar_ids = self._session_index.get(session_id, [])
            return [self._clarifications[cid] for cid in clar_ids if cid in self._clarifications]

    def build_prompt(self, matches: List[str], action: str = "use") -> str:
        """Build a deterministic clarification prompt from multiple matches.

        Args:
            matches: List of candidate strings (e.g. filenames).
            action: Verb to describe the action (e.g. 'open', 'delete').

        Returns:
            Human-readable clarification prompt string.
        """
        if not matches:
            return "Which item did you mean?"
        if len(matches) == 1:
            return f'Did you mean "{matches[0]}"?'
        options_text = ", ".join(f'"{m}"' for m in matches[:-1])
        return f"Did you mean to {action} {options_text} or \"{matches[-1]}\"?"

    def clear_session(self, session_id: str) -> None:
        """Remove all clarification records for a session.

        Args:
            session_id: Session to clear.
        """
        with self._lock:
            clar_ids = self._session_index.pop(session_id, [])
            for cid in clar_ids:
                self._clarifications.pop(cid, None)
