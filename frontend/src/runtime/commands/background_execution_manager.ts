/**
 * Background Execution Manager Implementation (Phase 16.6.6).
 *
 * Implements IBackgroundExecutionManager managing asynchronous background execution
 * of command requests, background task state transitions, completion tracking,
 * failures, cancellation, retry scheduling with backoff factors, metrics, and health evaluation.
 */

import {
  BackgroundTask,
  BackgroundDiagnostics,
  BackgroundHealth,
  BackgroundStatistics,
  CommandExecutionRequest,
  CommandExecutionStatus,
  createBackgroundTask,
  createBackgroundDiagnostics,
  createBackgroundHealth,
  createBackgroundStatistics,
} from './models';
import { CommandValidationException } from './exceptions';
import { ICommandPipeline, IBackgroundExecutionManager } from './interfaces';

export class BackgroundExecutionManager implements IBackgroundExecutionManager {
  private readonly _pipeline: ICommandPipeline;
  private readonly _tasks = new Map<string, BackgroundTask>();
  private readonly _activeTimers = new Map<string, any>();

  private _totalSubmitted = 0;
  private _completedTasks = 0;
  private _failedTasks = 0;
  private _cancelledTasks = 0;
  private _retryAttempts = 0;

  constructor(pipeline: ICommandPipeline) {
    this._pipeline = pipeline;
  }

  public async submitBackgroundTask(request: CommandExecutionRequest): Promise<BackgroundTask> {
    if (!request) {
      throw new CommandValidationException('Background request cannot be null or undefined.');
    }

    this._totalSubmitted++;

    const task = createBackgroundTask({
      commandId: request.commandId,
      request,
      status: 'pending',
      submittedAt: new Date().toISOString(),
      retries: 0,
      maxRetries: 3,
    });

    this._tasks.set(task.taskId, task);
    this.runTaskAsync(task.taskId);

    return task;
  }

  public cancelBackgroundTask(taskId: string): boolean {
    if (!taskId) return false;
    const task = this._tasks.get(taskId);
    if (!task || task.status === 'completed' || task.status === 'cancelled' || task.status === 'failed') {
      return false;
    }

    const timer = this._activeTimers.get(taskId);
    if (timer) {
      clearTimeout(timer);
      this._activeTimers.delete(taskId);
    }

    const updated = createBackgroundTask({
      taskId: task.taskId,
      commandId: task.commandId,
      request: task.request,
      status: 'cancelled',
      submittedAt: task.submittedAt,
      startedAt: task.startedAt,
      completedAt: new Date().toISOString(),
      durationMs: task.durationMs,
      retries: task.retries,
      maxRetries: task.maxRetries,
      error: 'Task cancelled by user.',
    });

    this._tasks.set(taskId, updated);
    this._cancelledTasks++;
    return true;
  }

  public backgroundTasks(): ReadonlyArray<BackgroundTask> {
    return Object.freeze(Array.from(this._tasks.values()));
  }

  public statistics(): BackgroundStatistics {
    const active = Array.from(this._tasks.values()).filter(
      (t) => t.status === 'pending' || t.status === 'running'
    ).length;

    return createBackgroundStatistics({
      totalSubmitted: this._totalSubmitted,
      activeTasks: active,
      completedTasks: this._completedTasks,
      failedTasks: this._failedTasks,
      cancelledTasks: this._cancelledTasks,
      retryAttempts: this._retryAttempts,
    });
  }

  public health(): BackgroundHealth {
    const stats = this.statistics();
    const failureRate =
      this._totalSubmitted > 0 ? Math.round((this._failedTasks / this._totalSubmitted) * 100) : 0;
    const healthy = failureRate <= 20;

    return createBackgroundHealth({
      healthy,
      activeTasks: stats.activeTasks,
      failureRate,
      message: healthy
        ? 'Background execution manager is operational.'
        : `Background execution manager elevated failure rate (${failureRate}%).`,
    });
  }

  public diagnostics(): BackgroundDiagnostics {
    return createBackgroundDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      activeTasksCount: this.statistics().activeTasks,
    });
  }

  public clear(): void {
    for (const timer of this._activeTimers.values()) {
      clearTimeout(timer);
    }
    this._activeTimers.clear();
    this._tasks.clear();
    this._totalSubmitted = 0;
    this._completedTasks = 0;
    this._failedTasks = 0;
    this._cancelledTasks = 0;
    this._retryAttempts = 0;
  }

  private runTaskAsync(taskId: string): void {
    const timer = setTimeout(() => this.executeTask(taskId), 0);
    this._activeTimers.set(taskId, timer);
  }

  private async executeTask(taskId: string): Promise<void> {
    const task = this._tasks.get(taskId);
    if (!task || task.status === 'cancelled') return;

    this._activeTimers.delete(taskId);

    const startPerf = performance ? performance.now() : Date.now();
    const startedAt = task.startedAt ?? new Date().toISOString();

    const running = createBackgroundTask({
      taskId: task.taskId,
      commandId: task.commandId,
      request: task.request,
      status: 'running',
      submittedAt: task.submittedAt,
      startedAt,
      completedAt: null,
      durationMs: task.durationMs,
      retries: task.retries,
      maxRetries: task.maxRetries,
    });

    this._tasks.set(taskId, running);

    try {
      const result = await this._pipeline.executePipeline(task.request);
      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);

      if (result.executionResult.status === CommandExecutionStatus.COMPLETED) {
        const completed = createBackgroundTask({
          taskId: task.taskId,
          commandId: task.commandId,
          request: task.request,
          status: 'completed',
          submittedAt: task.submittedAt,
          startedAt,
          completedAt: new Date().toISOString(),
          durationMs,
          retries: task.retries,
          maxRetries: task.maxRetries,
        });

        this._tasks.set(taskId, completed);
        this._completedTasks++;
      } else {
        throw new Error(result.executionResult.error?.message ?? 'Execution pipeline failed.');
      }
    } catch (err: any) {
      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);

      if (task.retries < task.maxRetries) {
        this._retryAttempts++;
        const retrying = createBackgroundTask({
          taskId: task.taskId,
          commandId: task.commandId,
          request: task.request,
          status: 'pending',
          submittedAt: task.submittedAt,
          startedAt: null,
          completedAt: null,
          durationMs,
          retries: task.retries + 1,
          maxRetries: task.maxRetries,
          error: err?.message,
        });

        this._tasks.set(taskId, retrying);

        // Exponential backoff retry
        const backoffMs = Math.pow(2, task.retries) * 100;
        const retryTimer = setTimeout(() => this.executeTask(taskId), backoffMs);
        this._activeTimers.set(taskId, retryTimer);
      } else {
        const failed = createBackgroundTask({
          taskId: task.taskId,
          commandId: task.commandId,
          request: task.request,
          status: 'failed',
          submittedAt: task.submittedAt,
          startedAt,
          completedAt: new Date().toISOString(),
          durationMs,
          retries: task.retries,
          maxRetries: task.maxRetries,
          error: err?.message || 'Max retries reached.',
        });

        this._tasks.set(taskId, failed);
        this._failedTasks++;
      }
    }
  }
}
