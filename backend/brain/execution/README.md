# Execution Engine & Task Management Subsystem

This package implements the **Execution Engine**, **Long-Running Task Subsystem**, and **Background Job Scheduler Subsystem** for Auralis. It coordinates the step-by-step dispatch of routed execution plans, observable long-running tasks, and scheduled recurring background jobs.

## Subsystem Responsibilities

1. **Sequential & Async Execution**: Coordinate execution sequences, ensuring step-by-step capability dispatch through the active system dispatcher.
2. **Long-Running Task Management**: Detect, register, queue, execute, track progress, pause, resume, cancel, recover, and persist long-running background tasks (`LongRunningTaskManager`).
3. **Task Progress & Event Notification**: Dispatch observable task progress events (`TASK_CREATED`, `TASK_STARTED`, `TASK_PROGRESS`, `TASK_COMPLETED`, `TASK_FAILED`, etc.) via `TaskEventDispatcher`.
4. **Background Job Scheduler**: Schedule one-time and recurring jobs (`ONCE`, `INTERVAL`, `DAILY`, `WEEKLY`, `MONTHLY`, `MANUAL`) with deterministic schedule calculations (`RecurringScheduleCalculator`), parameter validations (`RecurringTriggerValidator`), recovery, expiration rules, and retention cleanup policies (`BackgroundJobScheduler`).
5. **Runtime Monitoring & History**: Track operational execution histories, metrics (`ExecutionMetrics`), aggregated statistics (`ExecutionStatistics`), and background job metrics via `ExecutionMonitor`.
6. **Decision & Failure Recovery**: Evaluate execution decisions (`DecisionEngine`), formulate recovery plans (`FailureRecoveryEngine`), and manage interactive clarification sessions (`ClarificationEngine`).

> [!IMPORTANT]
> The Execution Engine and Scheduler operate thread-safely in-memory with non-blocking persistence hooks (`TaskPersistenceHook`, `BackgroundJobPersistenceHook`). They do not require external message queues (Celery, Redis, RabbitMQ) or cron libraries (APScheduler).

## Directory Structure

- [execution_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_engine.py): Step-by-step capability plan execution and scheduled job processing pipeline.
- [execution_state.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_state.py): Live execution session state tracking and progress snapshots.
- [execution_monitor.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_monitor.py): Metrics computation, event listener, and background scheduler statistics aggregation.
- [execution_validator.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_validator.py): Confirms capability requirements and plan structures.
- [execution_scheduler.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/execution_scheduler.py): Orders plan execution steps sequentially.
- [long_running_task_manager.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/long_running_task_manager.py): Long-running task detection, queueing, registration, progress tracking, persistence hooks, and recovery.
- [task_events.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/task_events.py): Observable event notification models and thread-safe listener dispatcher (`TaskEventDispatcher`).
- [background_job_scheduler.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/background_job_scheduler.py): Background job scheduler (`BackgroundJobScheduler`), trigger validator (`RecurringTriggerValidator`), schedule calculator (`RecurringScheduleCalculator`), and persistence hook protocol (`BackgroundJobPersistenceHook`).
- [decision_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/decision_engine.py): Interactive decision evaluation and intent approval checks.
- [failure_recovery_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/failure_recovery_engine.py): Diagnostic failure categorization and recovery plan formulation.
- [clarification_engine.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/execution/clarification_engine.py): Ambiguity clarification sessions and choice resolution.

