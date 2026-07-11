"""Capability matcher resolving intents/actions to brain capabilities."""

from __future__ import annotations

import logging
from core.intents import Intent
from .capability_registry import CapabilityRegistry
from .selector_rules import SelectorRules


class CapabilityMatcher:
    """Matches actions and intents to registered capabilities using selector rules."""

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        rules: SelectorRules | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes CapabilityMatcher.

        Args:
            registry: Registry of supported system capabilities.
            rules: Extension of routing rules.
            logger: Optional custom logger for matching diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._registry = registry or CapabilityRegistry(logger=self._logger)
        self._rules = rules or SelectorRules(logger=self._logger)

    def match_intent(self, intent: Intent, target: str | None = None) -> str:
        """Matches a system Intent to a registered capability name.

        Args:
            intent: The Intent to route.
            target: Optional target argument.

        Returns:
            The matched capability name, or 'Unknown' if not resolvable.
        """
        self._logger.debug("Matching intent to capability", extra={"intent": intent.value, "target": target})
        
        candidate_name = self._rules.route_intent(intent, target)
        
        if self._registry.has_capability(candidate_name):
            return candidate_name

        self._logger.warning(
            "Capability candidate is not in the registry; returning candidate name as fallback",
            extra={"candidate": candidate_name},
        )
        return candidate_name
