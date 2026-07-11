# Self-Correction & Recovery Subsystem

This package implements the **Self-Correction & Recovery** layer for Auralis. It detects execution failures and resolves strategies to recover execution.

## Responsibilities

1. **Analyze Failure Types**: The `FailureAnalyzer` maps raw error logs to canonical `FailureType` values (e.g. `APPLICATION_NOT_FOUND`, `FILE_NOT_FOUND`, `PERMISSION_DENIED`, `NETWORK_UNAVAILABLE`, `TIMEOUT`, `UNKNOWN`).
2. **Retrieve Fallbacks**: The `FallbackRegistry` maps failed execution targets to reliable system replacements (e.g., swapping VS Code with Cursor, or Chrome with Edge).
3. **Build Strategy**: The `RecoveryStrategyBuilder` prepares action execution plans to perform remediation.
4. **Execute Safe Recovery**: The `RecoveryEngine` executes recovery steps through the dispatcher, respecting user-confirmation boundaries for sensitive operations.

> [!IMPORTANT]
> To comply with safety criteria, recovery strategies will never perform destructive actions (deletion or modifications) automatically. Mappings tagged as requiring confirmation will halt and await user approval.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/recovery/models.py): Defines structured recovery schemas (`FailureType`, `FallbackOption`, `RecoveryStrategy`, `RecoveryResult`).
- [fallback_registry.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/recovery/fallback_registry.py): Stores target alias replacement options.
- [failure_analyzer.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/recovery/failure_analyzer.py): Classifies raw exception messages.
- [recovery_strategy.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/recovery/recovery_strategy.py): Standardizes actions for categorized failures.
- [recovery_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/recovery/recovery_engine.py): Manages the recovery and remediation execution pipeline.
