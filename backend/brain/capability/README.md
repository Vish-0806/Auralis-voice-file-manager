# Capability Selection Subsystem

This package implements the **Capability Selection** layer for Auralis. It maps execution steps and actions to the correct registered capability interfaces.

## Responsibilities

1. **Maintain Registry**: Store user-friendly mappings of capabilities to system capability identifiers. Supporting default capabilities (`File`, `Desktop`, `Voice`, `Workflow`) and future expansions (`Browser`, `Developer`, `Memory`).
2. **Apply Selector Rules**: Evaluate rule-based constraints matching intents, target strings, and descriptive indicators to candidate capability slots.
3. **Match Intents**: Verify candidate capability targets against the active capability registry, resolving fallbacks for unknown intents.
4. **Produce Routed Plans**: Return a `RoutedExecutionPlan` subclassing the core `ExecutionPlan` containing detailed capability routing maps (`CapabilityRoute`) for every step.

> [!IMPORTANT]
> The Capability Selection module remains independent from runtime execution, monitoring, or rollback handling.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/capability/models.py): Defines structured capability mapping schemas (`CapabilitySelection`, `CapabilityRoute`, `CapabilityRequirement`, `RoutedExecutionPlan`).
- [capability_registry.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/capability/capability_registry.py): Maps name aliases to core capability system identifiers.
- [selector_rules.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/capability/selector_rules.py): Implements intent-to-capability routing policy logic.
- [capability_matcher.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/capability/capability_matcher.py): Intersects rules against the active registry.
- [capability_selector.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/capability/capability_selector.py): Coordinates capability selection for single plans or multi-step sequences.
