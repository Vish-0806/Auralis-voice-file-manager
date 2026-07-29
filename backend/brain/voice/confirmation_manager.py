"""Confirmation Manager for the Auralis Voice Orchestration Engine (Phase 9.6).

Manages the lifecycle of voice confirmation workflows.
Thread-safe, deterministic. No LLM, no filesystem interaction.
"""

import logging
import threading
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from brain.voice.voice_models import ConfirmationStatus, VoiceConfirmation

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS: float = 30.0


class ConfirmationManager:
    """Thread-safe manager for voice confirmation workflows.

    Responsibilities:
    - Issue confirmation prompts and track their lifecycle.
    - Accept, reject, cancel, or time-out pending confirmations.
    - Maintain per-session history.
    """

    def __init__(self, default_timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS) -> None:
        """Initialises ConfirmationManager.

        Args:
            default_timeout_seconds: Default expiry window for confirmations.
        """
        self._lock = threading.RLock()
        self._default_timeout = default_timeout_seconds
        # confirmation_id → VoiceConfirmation
        self._confirmations: Dict[str, VoiceConfirmation] = {}
        # session_id → [confirmation_id, ...]
        self._session_index: Dict[str, List[str]] = {}
        logger.debug("ConfirmationManager initialized timeout=%.1fs", default_timeout_seconds)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_confirmation(
        self,
        session_id: str,
        prompt: str,
        command_id: str = "",
        timeout_seconds: Optional[float] = None,
    ) -> VoiceConfirmation:
        """Create and store a new pending confirmation.

        Args:
            session_id: Session requesting confirmation.
            prompt: Human-readable confirmation question.
            command_id: Associated command ID.
            timeout_seconds: Override default timeout.

        Returns:
            Immutable :class:`VoiceConfirmation` in PENDING state.
        """
        with self._lock:
            conf_id = f"conf-{uuid.uuid4().hex[:8]}"
            timeout = timeout_seconds if timeout_seconds is not None else self._default_timeout
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=timeout)

            confirmation = VoiceConfirmation(
                confirmation_id=conf_id,
                session_id=session_id,
                command_id=command_id,
                prompt=prompt,
                status=ConfirmationStatus.PENDING,
                timeout_seconds=timeout,
                created_at=now,
                expires_at=expires_at,
            )
            self._confirmations[conf_id] = confirmation
            self._session_index.setdefault(session_id, []).append(conf_id)
            logger.info(
                "Confirmation Requested: session_id=%s confirmation_id=%s",
                session_id, conf_id,
            )
            return confirmation

    def accept(self, confirmation_id: str) -> VoiceConfirmation:
        """Mark a confirmation as ACCEPTED.

        Args:
            confirmation_id: Confirmation to accept.

        Returns:
            Updated immutable :class:`VoiceConfirmation`.
        """
        return self._resolve(confirmation_id, ConfirmationStatus.ACCEPTED, response=True)

    def reject(self, confirmation_id: str) -> VoiceConfirmation:
        """Mark a confirmation as REJECTED.

        Args:
            confirmation_id: Confirmation to reject.

        Returns:
            Updated immutable :class:`VoiceConfirmation`.
        """
        return self._resolve(confirmation_id, ConfirmationStatus.REJECTED, response=False)

    def cancel(self, confirmation_id: str) -> VoiceConfirmation:
        """Mark a confirmation as CANCELLED.

        Args:
            confirmation_id: Confirmation to cancel.

        Returns:
            Updated immutable :class:`VoiceConfirmation`.
        """
        return self._resolve(confirmation_id, ConfirmationStatus.CANCELLED)

    def check_timeouts(self) -> List[VoiceConfirmation]:
        """Scan all PENDING confirmations and mark expired ones as TIMED_OUT.

        Returns:
            List of confirmations that were just timed-out.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            timed_out: List[VoiceConfirmation] = []
            for conf_id, conf in list(self._confirmations.items()):
                if conf.status == ConfirmationStatus.PENDING:
                    if conf.expires_at and now > conf.expires_at:
                        updated = conf.model_copy(update={
                            "status": ConfirmationStatus.TIMED_OUT,
                            "resolved_at": now,
                        })
                        self._confirmations[conf_id] = updated
                        timed_out.append(updated)
                        logger.info(
                            "Confirmation timed out: confirmation_id=%s session_id=%s",
                            conf_id, conf.session_id,
                        )
            return timed_out

    def get_confirmation(self, confirmation_id: str) -> Optional[VoiceConfirmation]:
        """Return the confirmation by ID, or None if not found.

        Also lazily checks timeout before returning.

        Args:
            confirmation_id: ID to look up.

        Returns:
            :class:`VoiceConfirmation` or None.
        """
        with self._lock:
            conf = self._confirmations.get(confirmation_id)
            if conf is None:
                return None
            # Lazy timeout check
            if conf.status == ConfirmationStatus.PENDING and conf.expires_at:
                if datetime.now(timezone.utc) > conf.expires_at:
                    conf = conf.model_copy(update={
                        "status": ConfirmationStatus.TIMED_OUT,
                        "resolved_at": datetime.now(timezone.utc),
                    })
                    self._confirmations[confirmation_id] = conf
            return conf

    def get_history(self, session_id: str) -> List[VoiceConfirmation]:
        """Return all confirmations for a session.

        Args:
            session_id: Session to look up.

        Returns:
            List of :class:`VoiceConfirmation` objects.
        """
        with self._lock:
            conf_ids = self._session_index.get(session_id, [])
            return [self._confirmations[cid] for cid in conf_ids if cid in self._confirmations]

    def clear_session(self, session_id: str) -> None:
        """Remove all confirmation records for a session.

        Args:
            session_id: Session to clear.
        """
        with self._lock:
            conf_ids = self._session_index.pop(session_id, [])
            for cid in conf_ids:
                self._confirmations.pop(cid, None)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _resolve(
        self,
        confirmation_id: str,
        status: ConfirmationStatus,
        response: Optional[bool] = None,
    ) -> VoiceConfirmation:
        """Apply a resolution status to a confirmation.

        Args:
            confirmation_id: Target confirmation.
            status: Resolution status to apply.
            response: Optional boolean response (True=accepted, False=rejected).

        Returns:
            Updated :class:`VoiceConfirmation`.
        """
        with self._lock:
            conf = self._confirmations.get(confirmation_id)
            if conf is None:
                # Return a minimal failed record
                logger.warning("ConfirmationManager._resolve: unknown confirmation_id=%s", confirmation_id)
                return VoiceConfirmation(
                    confirmation_id=confirmation_id,
                    status=status,
                    metadata={"error": "not_found"},
                )

            if conf.status != ConfirmationStatus.PENDING:
                logger.warning(
                    "ConfirmationManager._resolve: confirmation already resolved id=%s status=%s",
                    confirmation_id, conf.status,
                )
                return conf

            updated = conf.model_copy(update={
                "status": status,
                "response": response,
                "resolved_at": datetime.now(timezone.utc),
            })
            self._confirmations[confirmation_id] = updated

            if status == ConfirmationStatus.ACCEPTED:
                logger.info("Confirmation Accepted: confirmation_id=%s", confirmation_id)
            elif status == ConfirmationStatus.REJECTED:
                logger.info("Confirmation Rejected: confirmation_id=%s", confirmation_id)
            else:
                logger.info("Confirmation resolved status=%s id=%s", status, confirmation_id)

            return updated
