# Task Planning Subsystem

This package implements the **Dynamic Task Planning** subsystem for Auralis. It converts structured `ReasoningResult` details into optimized, runnable core `ExecutionPlan` instances.

## Responsibilities

1. **Receive ReasoningResult**: Accept task parameters, constraints, and priorities from the Reasoning Engine.
2. **Generate Steps**: Dynamically build individual execution steps (`ExecutionStep`) from user objectives and unsatisfied environmental dependencies (e.g. enabling WiFi, creating folders).
3. **Resolve Dependencies**: Execute topological sorting via Kahn's algorithm, establishing execution orders and preventing circular logic.
4. **Optimize Sequences**: Deduplicate actions and group independent steps for parallel execution path options.
5. **Bridge Dispatcher**: Compile multi-step plans into transient workflows registered in `WorkflowRegistry` dynamically so the default `WorkflowEngine` capability can invoke them.

> [!IMPORTANT]
> The Task Planner does not handle execution tracking, retries, rollbacks, or recovery logic. It maps out the plan, which is handed directly to the Dispatcher.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/planning/models.py): Defines structured planning representations (`ExecutionStep`, `ExecutionDependency`, `ExecutionSequence`).
- [plan_builder.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/planning/plan_builder.py): Performs dynamic step construction based on objectives and unsatisfied constraints.
- [dependency_resolver.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/planning/dependency_resolver.py): Executes dependency checking and topological order resolution.
- [plan_optimizer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/planning/plan_optimizer.py): Deduplicates actions and groups parallel steps.
- [task_planner.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/planning/task_planner.py): Coordinates the overall dynamic planning pipeline.
