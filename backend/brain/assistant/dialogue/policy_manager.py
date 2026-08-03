"""Policy Manager implementation for Auralis (Phase 13.3).

Evaluates dialogue policies, detects clarification/confirmation requirements,
and determines response modes without invoking AI. Thread-safe using threading.RLock().
"""

import logging
import threading
from typing import Optional

from brain.assistant.dialogue.interfaces import IDialoguePolicyManager
from brain.assistant.dialogue.models import (
    DialogueAction,
    DialogueDecision,
    DialogueMode,
    DialoguePolicy,
    DialogueSession,
    DialogueTurn,
)

logger = logging.getLogger(__name__)

# Action keywords triggering confirmation or termination
_DESTRUCTIVE_KEYWORDS = {"delete", "remove", "wipe", "format", "purge", "destroy"}
_TERMINATE_KEYWORDS = {"cancel", "stop", "exit", "quit", "abort"}


class PolicyManager(IDialoguePolicyManager):
    """Thread-safe policy evaluation engine for dialogue flow decisions."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def evaluate(
        self,
        session: DialogueSession,
        turn: DialogueTurn,
        policy: Optional[DialoguePolicy] = None,
    ) -> DialogueDecision:
        """Evaluate dialogue policy rules deterministically against current turn and session context."""
        with self._lock:
            pol = policy or session.policy or DialoguePolicy()
            user_text = (turn.user_input or "").strip().lower()
            tokens = set(user_text.split())

            # 1. Detect Low Confidence Clarification Requirement
            if turn.confidence < pol.auto_clarify_threshold:
                return DialogueDecision(
                    action=DialogueAction.CLARIFY,
                    mode=session.mode,
                    requires_clarification=True,
                    clarification_prompt=f"Confidence low ({turn.confidence:.2f}). Could you please clarify your request?",
                    confidence=turn.confidence,
                    reason="Turn confidence below auto_clarify_threshold",
                )

            # 2. Detect Termination Request
            if any(k in tokens for k in _TERMINATE_KEYWORDS):
                return DialogueDecision(
                    action=DialogueAction.TERMINATE,
                    mode=session.mode,
                    confidence=turn.confidence,
                    reason="User requested session termination",
                )

            # 3. Detect Destructive Confirmation Requirement
            if pol.require_confirmation_for_destructive and any(k in tokens for k in _DESTRUCTIVE_KEYWORDS):
                return DialogueDecision(
                    action=DialogueAction.CONFIRM,
                    mode=session.mode,
                    requires_confirmation=True,
                    confirmation_prompt=f"Confirmation required: Are you sure you want to perform action: '{turn.user_input}'?",
                    confidence=turn.confidence,
                    reason="Destructive keyword detected requiring confirmation",
                )

            # 4. Standard Response / Execution Decision
            action = DialogueAction.RESPOND
            if turn.metadata.get("executable") or "run" in tokens or "execute" in tokens:
                action = DialogueAction.EXECUTE

            return DialogueDecision(
                action=action,
                mode=session.mode or pol.default_mode,
                requires_clarification=False,
                requires_confirmation=False,
                confidence=turn.confidence,
                reason="Standard policy evaluation completed",
            )
