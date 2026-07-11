# Progress Monitoring Subsystem

This package implements the **Progress Monitoring** and metrics collection layer for Auralis. It observes active execution runs, broadcasts events, and tracks metrics.

## Responsibilities

1. **Calculate Completion**: The `ExecutionTracker` computes elapsed execution times, remaining time estimations, and completion percentages.
2. **Collect Performance Metrics**: The `MetricsCollector` records step execution duration patterns, step success/failure outcomes, and recovery trigger frequencies.
3. **Publish Updates**: The `EventStream` implements a callback subscription interface enabling clients (such as voice synthesis engines or user interfaces) to listen to execution events.
4. **Stall Warning Detection**: The `ProgressMonitor` checks step execution states to signal stall warnings if a running process hangs beyond expected durations.

> [!NOTE]
> The progress monitoring system remains strictly observational and has no ability to alter, retry, or cancel execution processes.

## Directory Structure

- [models.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/monitoring/models.py): Defines structured monitoring schemas (`ExecutionEvent`, `ExecutionProgress`, `ExecutionMetrics`, `ProgressUpdate`).
- [execution_tracker.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/monitoring/execution_tracker.py): Tracks session progress.
- [metrics_collector.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/monitoring/metrics_collector.py): Stores step performance counts.
- [event_stream.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/monitoring/event_stream.py): Distributes status envelopes.
- [progress_monitor.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/backend/brain/monitoring/progress_monitor.py): Coordinates tracking triggers.
