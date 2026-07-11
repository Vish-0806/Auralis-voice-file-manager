"""Capability Selector orchestrator mapping execution plans to capabilities."""

from __future__ import annotations

import logging
from core.models import ExecutionPlan as CoreExecutionPlan
from core.intents import Intent
from automation.workflow.workflow_registry import WorkflowRegistry

from .models import RoutedExecutionPlan, CapabilityRoute, CapabilitySelection, CapabilityRequirement
from .capability_registry import CapabilityRegistry
from .capability_matcher import CapabilityMatcher


class CapabilitySelector:
    """Routes execution plans and workflow steps to their target system capabilities."""

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        matcher: CapabilityMatcher | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes CapabilitySelector.

        Args:
            registry: The CapabilityRegistry.
            matcher: The CapabilityMatcher.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._registry = registry or CapabilityRegistry(logger=self._logger)
        self._matcher = matcher or CapabilityMatcher(registry=self._registry, logger=self._logger)

    def select_capabilities(self, plan: CoreExecutionPlan) -> RoutedExecutionPlan:
        """Selects capabilities for each step in an ExecutionPlan.

        Args:
            plan: The incoming core ExecutionPlan.

        Returns:
            A RoutedExecutionPlan containing capability routes and requirements.
        """
        self._logger.info("Starting capability selection", extra={"intent": plan.intent.value, "target": plan.target})

        routes: list[CapabilityRoute] = []
        selections: list[CapabilitySelection] = []
        requirements: list[CapabilityRequirement] = []

        if plan.intent == Intent.RUN_WORKFLOW and plan.target:
            registry = WorkflowRegistry(logger=self._logger)
            wf_def = registry.get_workflow(plan.target)

            if wf_def:
                for idx, step in enumerate(wf_def.steps):
                    step_id = f"step_{idx + 1}"
                    cap_name = self._matcher.match_intent(step.intent, step.target)
                    routes.append(
                        CapabilityRoute(
                            step_id=step_id,
                            intent=step.intent,
                            capability_name=cap_name,
                        )
                    )
                    selections.append(
                        CapabilitySelection(
                            intent=step.intent,
                            capability_name=cap_name,
                            confidence=plan.confidence,
                        )
                    )
            else:
                cap_name = self._matcher.match_intent(plan.intent, plan.target)
                routes.append(
                    CapabilityRoute(
                        step_id="main",
                        intent=plan.intent,
                        capability_name=cap_name,
                    )
                )
                selections.append(
                    CapabilitySelection(
                        intent=plan.intent,
                        capability_name=cap_name,
                        confidence=plan.confidence,
                    )
                )
        else:
            cap_name = self._matcher.match_intent(plan.intent, plan.target)
            routes.append(
                CapabilityRoute(
                    step_id="main",
                    intent=plan.intent,
                    capability_name=cap_name,
                )
            )
            selections.append(
                CapabilitySelection(
                    intent=plan.intent,
                    capability_name=cap_name,
                    confidence=plan.confidence,
                )
            )

        unique_caps = {route.capability_name for route in routes}
        for cap in unique_caps:
            requirements.append(
                CapabilityRequirement(
                    capability_name=cap,
                    reason=f"Required to execute routed step with capability: '{cap}'",
                )
            )

        routed_plan = RoutedExecutionPlan(
            intent=plan.intent,
            target=plan.target,
            parameters=plan.parameters.copy(),
            confidence=plan.confidence,
            routes=routes,
            selections=selections,
            requirements=requirements,
        )

        self._logger.info(
            "Capability selection completed",
            extra={
                "intent": plan.intent.value,
                "routes_count": len(routes),
                "required_capabilities": list(unique_caps),
            },
        )
        return routed_plan
