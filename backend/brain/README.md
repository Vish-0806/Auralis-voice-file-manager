# Auralis AI Brain

This directory contains the core **AI Brain** module of Auralis (Phase 5). The AI Brain is a modular, local-first request processing pipeline that translates natural language commands into verified, routed, and resilient multi-step executions.

## Subsystem Architecture

The AI Brain is structured as a series of independent, single-responsibility layers coordinated by a central controller:

```mermaid
graph TD
    Request[User Message / BrainRequest] --> Interpreter[Goal Interpreter]
    Interpreter --> |Goal Result| Reasoning[Reasoning Engine]
    Reasoning --> |Reasoning Result| Planner[Dynamic Task Planner]
    Planner --> |Core Execution Plan| Selector[Capability Selector]
    Selector --> |Routed Execution Plan| Executor[Multi-Step Execution Engine]
    
    subgraph Execution Coordination
        Executor <--> Recovery[Self-Correction & Recovery]
        Executor --> Progress[Progress Monitoring]
    end
    
    Executor --> |Action steps| Dispatcher[Action Dispatcher]
```

## Subsystems

| Directory | Subsystem | Purpose & Function |
| :--- | :--- | :--- |
| [goal/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/goal) | **Goal Interpreter** | Translates natural language messages into canonical Goal payloads with confidence scores. |
| [reasoning/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/reasoning) | **Reasoning Engine** | Evaluates matched goals to deduce target objectives, capability requirements, priority, and constraints. |
| [planning/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/planning) | **Dynamic Task Planner** | Formulates ordered steps topologically, prepending checks (e.g. creating directories) to satisfy plan constraints. |
| [capability/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/capability) | **Capability Selector** | Binds and routes plan execution steps to specific system capabilities (Desktop, File, etc.). |
| [execution/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution) | **Multi-Step Execution Engine** | Schedules step executions sequentially using execution context states. |
| [recovery/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/recovery) | **Self-Correction & Recovery** | Analyzes step failures, maps fallback strategies (e.g. launching Edge if Chrome is missing), and recovers steps. |
| [monitoring/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/monitoring) | **Progress Monitoring** | Observes execution status, provides percentage estimations, detects stalls, and records execution metrics. |
| [controller/](file:///c:/Users/Vishal S Naik/MyProjects/Auralis-voice-file-manager/backend/brain/controller) | **AI Brain Controller** | Orchestrates the entire pipeline, exposing the centralized execution gateway `process_request`. |

## Core Integration Flow

The AI Brain integrates seamlessly into Auralis' main entry point, `AuralisAssistant`:

1. When a request is received, the assistant wraps it into a `BrainRequest` and sends it to the `BrainController`.
2. The controller processes the request through the pipeline stages.
3. If the Goal Interpreter returns low confidence or an `UNKNOWN` goal classification, the controller bypasses the AI Brain and falls back to legacy rule-based execution.
4. If a step fails during execution, the Multi-Step Execution Engine intercepts the failure, invokes the Recovery Engine to apply safe remediations, and resumes execution seamlessly.
