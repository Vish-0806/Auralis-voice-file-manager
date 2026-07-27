"""Manages and parses user responses to clarification requests."""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

from brain.conversation_intelligence.models import PendingClarification

logger = logging.getLogger(__name__)


class ClarificationManager:
    """Evaluates user responses to clarify ambiguous options."""

    def resolve_clarification(
        self, user_response: str, pending: PendingClarification
    ) -> tuple[Optional[str], bool]:
        """Resolves user response against options.

        Returns:
            A tuple of (resolved_value, is_cancelled).
            - resolved_value: The selected candidate option path/name, or None if unmapped.
            - is_cancelled: True if the user explicitly cancelled the action.
        """
        response_lower = user_response.lower().strip()

        # Check for cancel signals
        cancel_words = ["cancel", "nevermind", "never mind", "stop", "abort"]
        if any(word == response_lower for word in cancel_words):
            logger.info("Clarification cancelled by the user.")
            return None, True

        # 1. Resolve Ordinals
        first_patterns = [r"\bfirst\b", r"\bone\b", r"\b1\b", r"\b1st\b", r"\bthe first one\b"]
        if any(re.search(pat, response_lower) for pat in first_patterns):
            if len(pending.options) >= 1:
                return pending.options[0], False

        second_patterns = [r"\bsecond\b", r"\btwo\b", r"\b2\b", r"\b2nd\b", r"\bthe second one\b"]
        if any(re.search(pat, response_lower) for pat in second_patterns):
            if len(pending.options) >= 2:
                return pending.options[1], False

        third_patterns = [r"\bthird\b", r"\bthree\b", r"\b3\b", r"\b3rd\b", r"\bthe third one\b"]
        if any(re.search(pat, response_lower) for pat in third_patterns):
            if len(pending.options) >= 3:
                return pending.options[2], False

        last_patterns = [r"\blast\b", r"\bthe last one\b", r"\bthe last file\b"]
        if any(re.search(pat, response_lower) for pat in last_patterns):
            if len(pending.options) >= 1:
                return pending.options[-1], False

        # 2. Resolve by string matching against candidate options
        best_match = None
        best_match_score = 0

        for option in pending.options:
            opt_lower = option.lower()
            # If the user response matches the filename exactly or is a substring of the option
            filename = os.path.basename(option) if "/" in option or "\\" in option else option
            file_lower = filename.lower()

            if response_lower == opt_lower or response_lower == file_lower:
                return option, False

            # Check if user message contains a unique directory/part of the path
            parts = re.split(r"[/\\]", opt_lower)
            for part in parts:
                if part and part == response_lower:
                    return option, False

            # Substring match: if user response is in option or file
            if response_lower in opt_lower or response_lower in file_lower:
                score = len(response_lower)
                if score > best_match_score:
                    best_match = option
                    best_match_score = score

        if best_match:
            logger.info("Resolved clarification using substring match: '%s'", best_match)
            return best_match, False

        # If user typed an index directly (e.g. "3")
        try:
            val = int(response_lower)
            if 1 <= val <= len(pending.options):
                return pending.options[val - 1], False
        except ValueError:
            pass

        # Could not resolve
        logger.warning("Failed to resolve response '%s' against options: %s", user_response, pending.options)
        return None, False
