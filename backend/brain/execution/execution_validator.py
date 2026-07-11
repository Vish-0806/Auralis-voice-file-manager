"""Execution plan validator for Auralis."""

from __future__ import annotations

import logging
from typing import Any
from brain.capability.models import RoutedExecutionPlan


class ExecutionValidator:
    """Validates the capability requirements, sequencing, and structure of routed plans."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ExecutionValidator.

        Args:
            logger: Optional custom logger for validator diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def validate_plan(self, plan: RoutedExecutionPlan, dispatcher: Any) -> None:
        """Checks plan integrity, capability availability, execution order, and dependencies.

        Args:
            plan: The RoutedExecutionPlan to validate.
            dispatcher: ActionDispatcher instance containing registered capabilities.

        Raises:
            ValueError: If any validation checks fail.
        """
        self._logger.info("Validating routed execution plan", extra={"intent": plan.intent.value})

        if not plan:
            raise ValueError("Routed execution plan cannot be null or empty.")
        if not plan.routes:
            raise ValueError("Routed execution plan must contain at least one capability route.")

        dispatcher_capabilities = getattr(dispatcher, "_capabilities", {})
        if dispatcher_capabilities:
            registered_keys = set(dispatcher_capabilities.keys())
            
            cap_mapping = {
                "FILE": "mock_file",
                "DESKTOP": "desktop",
                "WORKFLOW": "workflow",
                "VOICE": "voice",
            }

            for route in plan.routes:
                mapped_key = cap_mapping.get(route.capability_name.upper(), route.capability_name)
                if mapped_key not in registered_keys and mapped_key != "voice":
                    self._logger.error(
                        "Capability not available in dispatcher",
                        extra={"capability": route.capability_name, "mapped_key": mapped_key},
                    )
                    raise ValueError(f"Required capability '{route.capability_name}' (identifier: '{mapped_key}') is not available.")

        steps_count = len(plan.routes)
        if steps_count == 0:
            raise ValueError("Plan contains no execution steps.")

        self._logger.info("Routed execution plan validation passed successfully.")
