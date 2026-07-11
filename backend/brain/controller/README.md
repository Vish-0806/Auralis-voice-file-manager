# AI Brain Controller

This package implements the **AI Brain Controller** orchestrator for Auralis. It coordinates all Phase 5 AI Brain subsystems into one unified, modular request processing pipeline.

## Responsibilities

1. **Subsystem Coordination**: Connects the Goal Interpreter, Reasoning Engine, Dynamic Task Planner, Capability Selector, Execution Engine, Recovery Engine, and Progress Monitor.
2. **Centralized Configuration**: Holds config schemas (`BrainConfig`) for confidence levels, timeout limits, scheduling modes, and fallback mappings.
3. **Execution Auditing**: Manages the dynamic `BrainRegistry` enabling modules to self-register.
4. **Execution Pipeline**: Integrates directly into Auralis' entry point `AuralisAssistant` to route user messages through the complete pipeline, falling back to rule-based execution.

## Directory Structure

- [models.py](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/models.py): Defines structured controller schemas (`BrainRequest`, `BrainResponse`, `BrainStatus`, `BrainExecution`).
- [brain_config.py](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_config.py): Brain configuration.
- [brain_registry.py](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_registry.py): Dynamic module mapper.
- [brain_pipeline.py](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_pipeline.py): Orchestrates modular request pipeline steps.
- [brain_controller.py](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller/brain_controller.py): Top-level orchestrator class.
