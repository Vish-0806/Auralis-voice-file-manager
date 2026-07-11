# Multi-Step Execution Engine

This package implements the **Multi-Step Execution Engine** subsystem for Auralis. It coordinates the step-by-step execution of routed plans through the active system dispatcher.

## Responsibilities

1. **Validate Integrity**: Verify plan constraints and ensure dispatcher registry has the required routed capability handlers.
2. **Sequential Scheduling**: Coordinate execution sequences, ensuring previous actions complete before proceeding to subsequent tasks.
3. **Audit Trails & History**: Track session records, status checks, and execution durations to support debugging and compliance metrics.
4. **Context Tracking**: Maintain active run IDs, current step pointer addresses, completed task queues, and result payloads.

> [!IMPORTANT]
> The Execution Engine does not attempt self-correction, execution retries, rollback routines, or semantic intent reasoning. It functions as a sequential executor for plans output by the Capability Selector.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/models.py): Defines execution tracking schemas (`ExecutionStatus`, `ExecutionRecord`, `ExecutionContext`, `ExecutionSummary`).
- [execution_context.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_context.py): Implements live session context trackers.
- [execution_history.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_history.py): Saves step operational histories.
- [execution_validator.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_validator.py): Confirms capability requirements and plan structures.
- [execution_scheduler.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_scheduler.py): Orders step Operational queues sequentially.
- [execution_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_engine.py): Manages the step-by-step dispatch pipeline.
