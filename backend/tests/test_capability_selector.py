"""Unit tests for the Auralis Capability Selector subsystem and core Planner integration."""

from __future__ import annotations

import os
from datetime import datetime, UTC
# pyrefly: ignore [missing-import]
import pytest

from core.models import AssistantRequest, ExecutionPlan as CoreExecutionPlan
from core.intents import Intent
from core.planner import Planner
from brain.capability.models import (
    CapabilityRoute,
    CapabilitySelection,
    CapabilityRequirement,
    RoutedExecutionPlan,
)
from brain.capability.capability_registry import CapabilityRegistry
from brain.capability.selector_rules import SelectorRules
from brain.capability.capability_matcher import CapabilityMatcher
from brain.capability.capability_selector import CapabilitySelector


# --- Models Validation Tests ---

def test_capability_models_validation():
    """Validates instantiation of capability routing and selection models."""
    route = CapabilityRoute(step_id="1", intent=Intent.MUTE, capability_name="Desktop")
    selection = CapabilitySelection(intent=Intent.MUTE, capability_name="Desktop", confidence=0.8)
    req = CapabilityRequirement(capability_name="Desktop", reason="Hardware audio control")

    plan = RoutedExecutionPlan(
        intent=Intent.MUTE,
        confidence=0.8,
        routes=[route],
        selections=[selection],
        requirements=[req],
    )

    assert plan.routes[0].capability_name == "Desktop"
    assert plan.selections[0].confidence == 0.8
    assert plan.requirements[0].capability_name == "Desktop"
    assert isinstance(plan, CoreExecutionPlan)  # Must evaluate to True for Dispatcher compatibility!


# --- Capability Registry Tests ---

def test_capability_registry():
    """Validates registration of defaults and dynamic capability additions."""
    registry = CapabilityRegistry()
    
    # Check default mappings
    assert registry.has_capability("File") is True
    assert registry.has_capability("Desktop") is True
    assert registry.has_capability("Voice") is True
    assert registry.has_capability("Workflow") is True
    assert registry.get_identifier("File") == "mock_file"

    # Register future/custom capabilities
    registry.register_capability("Browser", "browser_capability")
    registry.register_capability("Developer", "developer_capability")
    registry.register_capability("Memory", "memory_capability")

    assert registry.has_capability("Browser") is True
    assert registry.has_capability("Developer") is True
    assert registry.has_capability("Memory") is True
    assert registry.get_identifier("Browser") == "browser_capability"


# --- Selector Rules Tests ---

def test_selector_rules():
    """Validates intent mapping policies to capability names."""
    rules = SelectorRules()
    
    assert rules.route_intent(Intent.CREATE_FOLDER) == "File"
    assert rules.route_intent(Intent.OPEN_APPLICATION) == "Desktop"
    assert rules.route_intent(Intent.RUN_WORKFLOW) == "Workflow"
    assert rules.route_intent(Intent.LOCK_PC) == "Desktop"
    assert rules.route_intent(Intent.UNKNOWN) == "Unknown"

    # Future capability rule matching
    assert rules.route_intent(Intent.UNKNOWN, target="url") == "Browser"


# --- Capability Matcher Tests ---

def test_capability_matcher():
    """Validates capability resolving against the registry."""
    registry = CapabilityRegistry()
    matcher = CapabilityMatcher(registry=registry)

    # Valid matching
    assert matcher.match_intent(Intent.CREATE_FOLDER) == "File"
    assert matcher.match_intent(Intent.OPEN_APPLICATION) == "Desktop"

    # Unregistered/future capability matching handles safely
    assert matcher.match_intent(Intent.UNKNOWN, target="url") == "Browser"


# --- Capability Selector Tests ---

def test_capability_selector_routing():
    """Validates selector routes plans and workflow steps correctly."""
    selector = CapabilitySelector()

    # 1. Test routing a single-step plan
    plan_single = CoreExecutionPlan(intent=Intent.LOCK_PC, confidence=1.0)
    routed_single = selector.select_capabilities(plan_single)

    assert isinstance(routed_single, RoutedExecutionPlan)
    assert len(routed_single.routes) == 1
    assert routed_single.routes[0].step_id == "main"
    assert routed_single.routes[0].capability_name == "Desktop"
    assert len(routed_single.requirements) == 1
    assert routed_single.requirements[0].capability_name == "Desktop"

    # 2. Test routing a multi-step workflow plan (e.g. Study Mode)
    plan_workflow = CoreExecutionPlan(intent=Intent.RUN_WORKFLOW, target="Study Mode", confidence=0.9)
    routed_workflow = selector.select_capabilities(plan_workflow)

    assert len(routed_workflow.routes) == 3
    # Study Mode steps: Edge (Desktop), Mute (Desktop), Wifi (Desktop)
    assert all(r.capability_name == "Desktop" for r in routed_workflow.routes)
    assert routed_workflow.routes[0].step_id == "step_1"
    assert routed_workflow.routes[0].intent == Intent.OPEN_APPLICATION
    assert len(routed_workflow.requirements) == 1
    assert routed_workflow.requirements[0].capability_name == "Desktop"


# --- Core Planner Integration Test ---

def test_planner_capability_routing_integration():
    """Validates that Planner creation returns a RoutedExecutionPlan containing routes."""
    planner = Planner()
    req = AssistantRequest(
        message="lock pc",
        source="test",
        timestamp=datetime.now(UTC)
    )
    
    plan = planner.create_plan(req)
    
    # Verify that plan is routed correctly
    assert isinstance(plan, RoutedExecutionPlan)
    assert len(plan.routes) == 1
    assert plan.routes[0].capability_name == "Desktop"
    assert len(plan.selections) == 1
    assert plan.selections[0].capability_name == "Desktop"
    assert plan.requirements[0].capability_name == "Desktop"
