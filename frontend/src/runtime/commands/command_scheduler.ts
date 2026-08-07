/**
 * Command Scheduler Implementation (Phase 16.6.6).
 *
 * Implements ICommandScheduler managing immediate, delayed, timestamp,
 * and recurring intervals execution of commands with pause, resume, cancellation,
 * schedule metrics collection, and health evaluation.
 */

import {
  CommandExecutionRequest,
  CommandSchedule,
  ScheduledCommand,
  SchedulingDiagnostics,
  ScheduleHealth,
  ScheduleStatistics,
  createCommandSchedule,
  createScheduledCommand,
  createSchedulingDiagnostics,
  createScheduleHealth,
  createScheduleStatistics,
} from './models';
import { CommandValidationException } from './exceptions';
import { ICommandPipeline, ICommandScheduler } from './interfaces';

export class CommandScheduler implements ICommandScheduler {
  private readonly _pipeline: ICommandPipeline;
  private readonly _schedules = new Map<string, ScheduledCommand>();
  private readonly _timerIds = new Map<string, any>();
  private _isPaused = false;

  private _totalScheduled = 0;
  private _executedSchedules = 0;
  private _cancelledSchedules = 0;
  private _recurringSchedules = 0;
  private _delayDurations: number[] = [];

  constructor(pipeline: ICommandPipeline) {
    this._pipeline = pipeline;
  }

  public async schedule(request: CommandExecutionRequest, delayMs?: number): Promise<ScheduledCommand> {
    if (!request) {
      throw new CommandValidationException('Scheduled request cannot be null or undefined.');
    }

    const type = delayMs !== undefined && delayMs > 0 ? 'delayed' : 'immediate';
    const schedule = createCommandSchedule({
      type,
      delayMs,
    });

    return this.createAndStartSchedule(request, schedule);
  }

  public async scheduleDelayed(request: CommandExecutionRequest, delayMs: number): Promise<ScheduledCommand> {
    if (delayMs === undefined || delayMs < 0) {
      throw new CommandValidationException('Delayed schedule requires a valid delay duration.');
    }

    const schedule = createCommandSchedule({
      type: 'delayed',
      delayMs,
    });

    return this.createAndStartSchedule(request, schedule);
  }

  public async scheduleRecurring(request: CommandExecutionRequest, intervalMs: number): Promise<ScheduledCommand> {
    if (intervalMs === undefined || intervalMs <= 0) {
      throw new CommandValidationException('Recurring schedule requires a positive interval duration.');
    }

    const schedule = createCommandSchedule({
      type: 'interval',
      intervalMs,
    });

    return this.createAndStartSchedule(request, schedule);
  }

  public cancelScheduled(scheduleId: string): boolean {
    if (!scheduleId) return false;
    const item = this._schedules.get(scheduleId);
    if (!item || item.status === 'cancelled' || item.status === 'completed') {
      return false;
    }

    this.clearTimer(scheduleId);

    const updated = createScheduledCommand({
      request: item.request,
      schedule: item.schedule,
      status: 'cancelled',
      nextRunTime: null,
      lastRunTime: item.lastRunTime,
      runCount: item.runCount,
      errorCount: item.errorCount,
    });

    this._schedules.set(scheduleId, updated);
    this._cancelledSchedules++;
    return true;
  }

  public pauseSchedule(): void {
    this._isPaused = true;
  }

  public resumeSchedule(): void {
    this._isPaused = false;
  }

  public listSchedules(): ReadonlyArray<ScheduledCommand> {
    return Object.freeze(Array.from(this._schedules.values()));
  }

  public statistics(): ScheduleStatistics {
    const active = Array.from(this._schedules.values()).filter(
      (s) => s.status === 'pending' || s.status === 'running'
    ).length;

    const avgDelay =
      this._delayDurations.length > 0
        ? this._delayDurations.reduce((a, b) => a + b, 0) / this._delayDurations.length
        : 0;

    return createScheduleStatistics({
      totalScheduled: this._totalScheduled,
      activeSchedules: active,
      executedSchedules: this._executedSchedules,
      cancelledSchedules: this._cancelledSchedules,
      recurringSchedules: this._recurringSchedules,
      averageScheduleDelayMs: Math.round(avgDelay * 100) / 100,
    });
  }

  public health(): ScheduleHealth {
    const stats = this.statistics();
    const totalRuns = stats.executedSchedules;
    const failures = Array.from(this._schedules.values()).reduce(
      (acc, val) => acc + val.errorCount,
      0
    );
    const failureRate = totalRuns > 0 ? Math.round((failures / (totalRuns + failures)) * 100) : 0;
    const healthy = failureRate <= 15;

    return createScheduleHealth({
      healthy,
      activeSchedules: stats.activeSchedules,
      failureRate,
      message: healthy
        ? 'Command scheduler is operational.'
        : `Command scheduler elevated failure rate (${failureRate}%).`,
    });
  }

  public diagnostics(): SchedulingDiagnostics {
    return createSchedulingDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      activeSchedulesCount: this.statistics().activeSchedules,
    });
  }

  public clear(): void {
    for (const scheduleId of this._timerIds.keys()) {
      this.clearTimer(scheduleId);
    }
    this._schedules.clear();
    this._timerIds.clear();
    this._isPaused = false;
    this._totalScheduled = 0;
    this._executedSchedules = 0;
    this._cancelledSchedules = 0;
    this._recurringSchedules = 0;
    this._delayDurations = [];
  }

  private createAndStartSchedule(
    request: CommandExecutionRequest,
    schedule: CommandSchedule,
  ): ScheduledCommand {
    this._totalScheduled++;
    const now = new Date();
    let nextRunTime: string | null = null;

    if (schedule.type === 'immediate') {
      nextRunTime = now.toISOString();
    } else if (schedule.type === 'delayed' && schedule.delayMs !== undefined) {
      nextRunTime = new Date(now.getTime() + schedule.delayMs).toISOString();
      this._delayDurations.push(schedule.delayMs);
    } else if (schedule.type === 'interval' && schedule.intervalMs !== undefined) {
      nextRunTime = new Date(now.getTime() + schedule.intervalMs).toISOString();
      this._recurringSchedules++;
    }

    const command = createScheduledCommand({
      scheduleId: schedule.scheduleId,
      request,
      schedule,
      status: 'pending',
      nextRunTime,
      lastRunTime: null,
      runCount: 0,
      errorCount: 0,
    });

    this._schedules.set(schedule.scheduleId, command);
    this.triggerSchedule(schedule.scheduleId);

    return command;
  }

  private triggerSchedule(scheduleId: string): void {
    const item = this._schedules.get(scheduleId);
    if (!item || item.status === 'cancelled') return;

    if (item.schedule.type === 'immediate') {
      // Execute immediately (asynchronously in next tick)
      const timer = setTimeout(() => this.executeTask(scheduleId), 0);
      this._timerIds.set(scheduleId, timer);
    } else if (item.schedule.type === 'delayed' && item.schedule.delayMs !== undefined) {
      const timer = setTimeout(() => this.executeTask(scheduleId), item.schedule.delayMs);
      this._timerIds.set(scheduleId, timer);
    } else if (item.schedule.type === 'interval' && item.schedule.intervalMs !== undefined) {
      const timer = setInterval(() => this.executeTask(scheduleId), item.schedule.intervalMs);
      this._timerIds.set(scheduleId, timer);
    }
  }

  private async executeTask(scheduleId: string): Promise<void> {
    const item = this._schedules.get(scheduleId);
    if (!item || item.status === 'cancelled') {
      return;
    }

    if (this._isPaused) {
      // Reschedule execution check to wait until resumed
      const timer = setTimeout(() => this.executeTask(scheduleId), 10);
      this._timerIds.set(scheduleId, timer);
      return;
    }

    // Update status to running
    const running = createScheduledCommand({
      request: item.request,
      schedule: item.schedule,
      status: 'running',
      nextRunTime: item.nextRunTime,
      lastRunTime: item.lastRunTime,
      runCount: item.runCount,
      errorCount: item.errorCount,
    });
    this._schedules.set(scheduleId, running);

    try {
      await this._pipeline.executePipeline(item.request);
      this._executedSchedules++;

      const isRecurring = item.schedule.type === 'interval';
      const completedStatus = isRecurring ? 'pending' : 'completed';

      const updated = createScheduledCommand({
        request: item.request,
        schedule: item.schedule,
        status: completedStatus,
        nextRunTime: isRecurring && item.schedule.intervalMs !== undefined
          ? new Date(Date.now() + item.schedule.intervalMs).toISOString()
          : null,
        lastRunTime: new Date().toISOString(),
        runCount: item.runCount + 1,
        errorCount: item.errorCount,
      });

      this._schedules.set(scheduleId, updated);
      if (!isRecurring) {
        this.clearTimer(scheduleId);
      }
    } catch (err) {
      const isRecurring = item.schedule.type === 'interval';
      const failedStatus = isRecurring ? 'pending' : 'failed';

      const updated = createScheduledCommand({
        request: item.request,
        schedule: item.schedule,
        status: failedStatus,
        nextRunTime: isRecurring && item.schedule.intervalMs !== undefined
          ? new Date(Date.now() + item.schedule.intervalMs).toISOString()
          : null,
        lastRunTime: new Date().toISOString(),
        runCount: item.runCount + 1,
        errorCount: item.errorCount + 1,
      });

      this._schedules.set(scheduleId, updated);
      if (!isRecurring) {
        this.clearTimer(scheduleId);
      }
    }
  }

  private clearTimer(scheduleId: string): void {
    const timer = this._timerIds.get(scheduleId);
    if (timer) {
      const item = this._schedules.get(scheduleId);
      if (item && item.schedule.type === 'interval') {
        clearInterval(timer);
      } else {
        clearTimeout(timer);
      }
      this._timerIds.delete(scheduleId);
    }
  }
}
