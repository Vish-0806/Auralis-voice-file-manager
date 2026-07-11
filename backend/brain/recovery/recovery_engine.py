"""Recovery engine orchestrator correcting runtime failures in Auralis."""

from __future__ import annotations

import logging
from typing import Any
from core.intents import Intent
from .models import FailureType, FallbackOption, RecoveryStrategy, RecoveryResult
from .fallback_registry import FallbackRegistry
from .failure_analyzer import FailureAnalyzer
from .recovery_strategy import RecoveryStrategyBuilder


class RecoveryEngine:
    """Detects failure causes, resolves strategies, and executes remediation plans."""

    def __init__(
        self,
        fallback_registry: FallbackRegistry | None = None,
        analyzer: FailureAnalyzer | None = None,
        strategy_builder: RecoveryStrategyBuilder | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the RecoveryEngine.

        Args:
            fallback_registry: Store of target mappings.
            analyzer: Error cause detector.
            strategy_builder: Action compiler.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._fallback_registry = fallback_registry or FallbackRegistry(logger=self._logger)
        self._analyzer = analyzer or FailureAnalyzer(logger=self._logger)
        self._strategy_builder = strategy_builder or RecoveryStrategyBuilder(logger=self._logger)

    def recover(
        self,
        step_id: str,
        intent: Intent,
        target: str | None,
        parameters: dict[str, Any],
        error_message: str,
        dispatcher: Any,
    ) -> RecoveryResult:
        """Identifies and executes remediation actions for a step execution failure.

        Args:
            step_id: The ID of the failed step.
            intent: The Intent that failed.
            target: The target argument that failed.
            parameters: Failed step parameters.
            error_message: Raw dispatcher error message.
            dispatcher: ActionDispatcher instance to run recovery actions.

        Returns:
            A RecoveryResult detailing success status and actions taken.
        """
        self._logger.info("Initiating failure recovery process", extra={"step_id": step_id, "error": error_message})

        failure_type = self._analyzer.analyze_failure(error_message)

        fallback = None
        if target:
            fallback = self._fallback_registry.get_fallback(target)

        if fallback and fallback.requires_confirmation:
            self._logger.warning(
                "Recovery aborted: User confirmation required for sensitive fallback",
                extra={"original": fallback.original, "fallback": fallback.fallback},
            )
            return RecoveryResult(
                success=False,
                strategy_applied="UserConfirmationRequired",
                remediation_actions=[],
                error="User confirmation required for recovery action",
            )

        strategy = self._strategy_builder.build_strategy(
            failure_type=failure_type,
            step_id=step_id,
            intent=intent,
            target=target,
            parameters=parameters,
            fallback=fallback,
        )

        if not strategy or not strategy.remediation_actions:
            self._logger.warning(
                "No automatic recovery strategy available for failure",
                extra={"failure_type": failure_type.value},
            )
            return RecoveryResult(
                success=False,
                error=f"No remediation strategy formulated for failure type: {failure_type.value}",
            )

        self._logger.info(
            "Executing recovery strategy actions",
            extra={"strategy_name": strategy.name, "actions_count": len(strategy.remediation_actions)},
        )

        executed_actions = []
        for action in strategy.remediation_actions:
            try:
                self._logger.info(
                    "Executing recovery remediation action plan",
                    extra={"intent": action.intent.value, "target": action.target},
                )
                result = dispatcher.dispatch(action)
                executed_actions.append(action)

                if not result.success:
                    self._logger.error(
                        "Remediation action failed",
                        extra={"intent": action.intent.value, "error": result.error},
                    )
                    return RecoveryResult(
                        success=False,
                        strategy_applied=strategy.name,
                        remediation_actions=executed_actions,
                        error=f"Remediation action failed: {result.error}",
                    )
            except Exception as exc:
                self._logger.error("Exception during recovery remediation execution", exc_info=exc)
                return RecoveryResult(
                    success=False,
                    strategy_applied=strategy.name,
                    remediation_actions=executed_actions,
                    error=f"Remediation encountered exception: {str(exc)}",
                )

        self._logger.info("Remediation execution completed successfully, step recovered")
        return RecoveryResult(
            success=True,
            strategy_applied=strategy.name,
            remediation_actions=executed_actions,
        )
