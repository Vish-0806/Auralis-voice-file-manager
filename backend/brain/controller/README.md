# AI Brain Controller

This package implements the **AI Brain Controller** orchestrator for Auralis. It coordinates all AI Brain subsystems, memory context builders, and reference resolvers into one unified, modular request processing pipeline.

## Responsibilities

1. **Context & Memory Aggregation**: Invokes `ContextBuilder` before planning to retrieve a structured, ranked `AssistantContext` (recent conversations, executions, latest context, user preferences, workspace profiles).
2. **Reference Resolution**: Runs `ReferenceResolver` prior to goal interpretation to replace ambiguous conversational pronouns (`it`, `them`) and spatial pointers (`same folder`, `same app`) with concrete entity paths.
3. **Subsystem Coordination**: Connects the Goal Interpreter, Reasoning Engine, Dynamic Task Planner, Capability Selector, Execution Engine, Recovery Engine, and Progress Monitor.
4. **Centralized Configuration**: Holds config schemas (`BrainConfig`) for confidence levels, timeout limits, scheduling modes, and fallback mappings.
5. **Execution Auditing**: Manages the dynamic `BrainRegistry` enabling modules to self-register.
6. **Execution Pipeline**: Integrates directly into Auralis' entry point `AuralisAssistant` to route user messages through the complete pipeline, falling back to rule-based execution.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/models.py): Defines structured controller schemas (`BrainRequest`, `BrainResponse`, `BrainStatus`, `BrainExecution`, `ResolvedRequest`).
- [brain_config.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_config.py): Brain configuration.
- [brain_registry.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_registry.py): Dynamic module mapper.
- [brain_pipeline.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_pipeline.py): Orchestrates modular request pipeline steps.
- [brain_controller.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_controller.py): Top-level orchestrator class.
