"""Fallback registry mapping failed targets to operational fallbacks in Auralis."""

from __future__ import annotations

import logging
from typing import Dict
from .models import FallbackOption


class FallbackRegistry:
    """Configurable store mapping components/applications to safe fallbacks."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the FallbackRegistry with default fallback paths.

        Args:
            logger: Optional custom logger for registry operations.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._fallbacks: Dict[str, FallbackOption] = {}
        self._register_defaults()

    def register_fallback(self, original: str, fallback: str, requires_confirmation: bool = False) -> None:
        """Registers a fallback mapping.

        Args:
            original: The name of the target that fails.
            fallback: The fallback target to execute instead.
            requires_confirmation: If True, prompt/confirm with user before executing.
        """
        original_upper = original.upper()
        self._fallbacks[original_upper] = FallbackOption(
            original=original,
            fallback=fallback,
            requires_confirmation=requires_confirmation,
        )
        self._logger.info(
            "Registered fallback mapping",
            extra={"original": original, "fallback": fallback, "requires_confirmation": requires_confirmation},
        )

    def get_fallback(self, original: str) -> FallbackOption | None:
        """Retrieves a fallback option mapping for a target name."""
        return self._fallbacks.get(original.upper())

    def has_fallback(self, original: str) -> bool:
        """Checks if a fallback option exists."""
        return original.upper() in self._fallbacks

    def _register_defaults(self) -> None:
        """Sets up baseline fallbacks."""
        self.register_fallback("Chrome", "Microsoft Edge", requires_confirmation=False)
        self.register_fallback("Google Chrome", "Microsoft Edge", requires_confirmation=False)
        self.register_fallback("VS Code", "Cursor", requires_confirmation=False)
        self.register_fallback("vscode", "Cursor", requires_confirmation=False)
        self.register_fallback("code", "Cursor", requires_confirmation=False)
        self.register_fallback("Admin Command Prompt", "Command Prompt", requires_confirmation=True)
