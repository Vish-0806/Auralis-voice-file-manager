"""Remediation strategy builder formulation for failed execution steps in Auralis."""

from __future__ import annotations

import logging
from typing import Any
from core.models import ExecutionPlan as CoreExecutionPlan
from core.intents import Intent
from .models import FailureType, FallbackOption, RecoveryStrategy


class RecoveryStrategyBuilder:
    """Builds actionable recovery strategy remediation actions."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes RecoveryStrategyBuilder.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def build_strategy(
        self,
        failure_type: FailureType,
        step_id: str,
        intent: Intent,
        target: str | None,
        parameters: dict[str, Any],
        fallback: FallbackOption | None,
    ) -> RecoveryStrategy | None:
        """Builds a RecoveryStrategy representing remediation steps.

        Args:
            failure_type: Classified FailureType.
            step_id: The failed step ID.
            intent: Failed step Intent.
            target: Failed step target.
            parameters: Failed step parameters.
            fallback: Optional FallbackOption mapping.

        Returns:
            A RecoveryStrategy containing remediation actions, or None.
        """
        actions: list[CoreExecutionPlan] = []
        name = f"Resolve_{failure_type.value}"

        if failure_type == FailureType.APPLICATION_NOT_FOUND:
            if fallback:
                self._logger.info(
                    "Resolving application missing failure using registered fallback",
                    extra={"target": target, "fallback": fallback.fallback},
                )
                actions.append(
                    CoreExecutionPlan(
                        intent=intent,
                        target=fallback.fallback,
                        parameters=parameters.copy(),
                        confidence=1.0,
                    )
                )
                return RecoveryStrategy(
                    failure_type=failure_type,
                    name=name,
                    description=f"Map missing app '{target}' to fallback app '{fallback.fallback}'",
                    remediation_actions=actions,
                )

        elif failure_type == FailureType.FILE_NOT_FOUND:
            self._logger.info("Resolving file missing failure via similar file search target lookup")
            actions.append(
                CoreExecutionPlan(
                    intent=Intent.UNKNOWN,
                    target=target,
                    parameters={"action": "search_similar_files", "original_step_id": step_id},
                    confidence=1.0,
                )
            )
            return RecoveryStrategy(
                failure_type=failure_type,
                name=name,
                description=f"Search for file alternatives for missing target '{target}'",
                remediation_actions=actions,
            )

        elif failure_type == FailureType.PERMISSION_DENIED:
            self._logger.info("Resolving permission failure via user confirmation request prompt")
            return RecoveryStrategy(
                failure_type=failure_type,
                name=name,
                description="Permission denied. Requires elevated session context confirmation.",
                remediation_actions=[],
            )

        elif failure_type == FailureType.NETWORK_UNAVAILABLE:
            self._logger.info("Resolving network unavailable failure via enabling wifi card")
            actions.append(
                CoreExecutionPlan(
                    intent=Intent.ENABLE_WIFI,
                    confidence=1.0,
                )
            )
            actions.append(
                CoreExecutionPlan(
                    intent=intent,
                    target=target,
                    parameters=parameters.copy(),
                    confidence=1.0,
                )
            )
            return RecoveryStrategy(
                failure_type=failure_type,
                name=name,
                description="Enable host WiFi connection and retry step.",
                remediation_actions=actions,
            )

        return None
