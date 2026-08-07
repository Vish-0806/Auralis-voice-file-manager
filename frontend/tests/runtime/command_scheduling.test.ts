import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  CommandExecutionRequest,
  CommandExecutor,
  CommandPipeline,
  CommandProvider,
  CommandQueue,
  CommandRegistry,
  CommandRuntime,
  CommandScheduler,
  BackgroundExecutionManager,
  createRetrySchedule,
  createExecutionWindow,
  createCommandSchedule,
  createScheduledCommand,
  createScheduledExecution,
  createScheduleStatistics,
  createScheduleHealth,
  createQueueEntry,
  createQueueStatistics,
  createQueueHealth,
  createBackgroundTask,
  createBackgroundExecution,
  createBackgroundStatistics,
  createBackgroundHealth,
  createSchedulingConfiguration,
  createSchedulingDiagnostics,
  createQueueDiagnostics,
  createBackgroundDiagnostics,
  resetCommandRuntime,
  resetCommandProvider,
  getCommandRuntime,
} from '../../src/runtime/commands';

describe('Phase 16.6.6 — Frontend Command Scheduling, Queue & Background Execution Engine', () => {
  let registry: CommandRegistry;
  let executor: CommandExecutor;
  let pipeline: CommandPipeline;
  let scheduler: CommandScheduler;
  let queue: CommandQueue;
  let bgManager: BackgroundExecutionManager;

  beforeEach(() => {
    resetCommandRuntime();
    resetCommandProvider();

    registry = new CommandRegistry();
    executor = new CommandExecutor(registry);
    // Setup simple command & handler
    registry.registerCommand({ id: 'test_cmd', displayName: 'Test Command' });
    executor.registerHandler('test_cmd', (args: any) => args.val ?? 'ok');

    pipeline = new CommandPipeline(executor, undefined, undefined, undefined, registry);
    scheduler = new CommandScheduler(pipeline);
    queue = new CommandQueue(10); // capacity 10 for testing overflow
    bgManager = new BackgroundExecutionManager(pipeline);
  });

  describe('1. Immutable Models & Factories', () => {
    it('should create immutable RetrySchedule model', () => {
      const retry = createRetrySchedule({ maxRetries: 5, delayMs: 2000 });
      expect(retry.maxRetries).toBe(5);
      expect(retry.delayMs).toBe(2000);
      expect(Object.isFrozen(retry)).toBe(true);
    });

    it('should create immutable ExecutionWindow model', () => {
      const window = createExecutionWindow({ startHour: 9, endHour: 17 });
      expect(window.startHour).toBe(9);
      expect(window.endHour).toBe(17);
      expect(Object.isFrozen(window)).toBe(true);
    });

    it('should create immutable CommandSchedule model', () => {
      const sched = createCommandSchedule({ type: 'delayed', delayMs: 500 });
      expect(sched.type).toBe('delayed');
      expect(sched.delayMs).toBe(500);
      expect(Object.isFrozen(sched)).toBe(true);
    });

    it('should create immutable ScheduledCommand model', () => {
      const req: CommandExecutionRequest = { commandId: 'test_cmd' };
      const sched = createCommandSchedule({ type: 'immediate' });
      const cmd = createScheduledCommand({ request: req, schedule: sched });
      expect(cmd.status).toBe('pending');
      expect(Object.isFrozen(cmd)).toBe(true);
    });

    it('should create immutable ScheduledExecution model', () => {
      const exec = createScheduledExecution({ scheduleId: 's1', commandId: 'c1' });
      expect(exec.scheduleId).toBe('s1');
      expect(Object.isFrozen(exec)).toBe(true);
    });

    it('should create immutable ScheduleStatistics & Health models', () => {
      const stats = createScheduleStatistics({ totalScheduled: 10 });
      const health = createScheduleHealth({ healthy: true });
      expect(stats.totalScheduled).toBe(10);
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(stats)).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable QueueEntry, Statistics & Health models', () => {
      const req: CommandExecutionRequest = { commandId: 'c1' };
      const entry = createQueueEntry({ request: req, priority: 5 });
      const stats = createQueueStatistics({ totalInsertions: 100 });
      const health = createQueueHealth({ healthy: true });

      expect(entry.priority).toBe(5);
      expect(stats.totalInsertions).toBe(100);
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(entry)).toBe(true);
      expect(Object.isFrozen(stats)).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable BackgroundTask, Execution, Statistics & Health models', () => {
      const req: CommandExecutionRequest = { commandId: 'c1' };
      const task = createBackgroundTask({ commandId: 'c1', request: req });
      const exec = createBackgroundExecution({ taskId: 't1', result: null as any });
      const stats = createBackgroundStatistics({ totalSubmitted: 10 });
      const health = createBackgroundHealth({ healthy: true });

      expect(task.status).toBe('pending');
      expect(exec.taskId).toBe('t1');
      expect(stats.totalSubmitted).toBe(10);
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(task)).toBe(true);
      expect(Object.isFrozen(exec)).toBe(true);
      expect(Object.isFrozen(stats)).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable SchedulingConfiguration & Diagnostics models', () => {
      const config = createSchedulingConfiguration({ maxQueueSize: 50 });
      const diag1 = createSchedulingDiagnostics({
        statistics: createScheduleStatistics(),
        health: createScheduleHealth(),
      });
      const diag2 = createQueueDiagnostics({
        statistics: createQueueStatistics(),
        health: createQueueHealth(),
      });
      const diag3 = createBackgroundDiagnostics({
        statistics: createBackgroundStatistics(),
        health: createBackgroundHealth(),
      });

      expect(config.maxQueueSize).toBe(50);
      expect(diag1.statistics).toBeDefined();
      expect(diag2.health).toBeDefined();
      expect(diag3.statistics).toBeDefined();
      expect(Object.isFrozen(config)).toBe(true);
      expect(Object.isFrozen(diag1)).toBe(true);
      expect(Object.isFrozen(diag2)).toBe(true);
      expect(Object.isFrozen(diag3)).toBe(true);
    });
  });

  describe('2. Command Scheduler Engine', () => {
    it('should schedule and execute task immediately', async () => {
      vi.useFakeTimers();
      const req: CommandExecutionRequest = { commandId: 'test_cmd', args: { val: 'hello' } };

      const schedCmd = await scheduler.schedule(req);
      expect(schedCmd.status).toBe('pending');
      expect(scheduler.statistics().totalScheduled).toBe(1);

      // Fast-forward timeout macro-task
      await vi.runOnlyPendingTimersAsync();

      const list = scheduler.listSchedules();
      expect(list[0].status).toBe('completed');
      expect(list[0].runCount).toBe(1);
      expect(scheduler.statistics().executedSchedules).toBe(1);
      vi.useRealTimers();
    });

    it('should schedule execution after configurable delays', async () => {
      vi.useFakeTimers();
      const req: CommandExecutionRequest = { commandId: 'test_cmd', args: { val: 'delayed' } };

      const schedCmd = await scheduler.scheduleDelayed(req, 1000);
      expect(schedCmd.status).toBe('pending');

      // Fast forward 500ms - task should still be pending
      await vi.advanceTimersByTimeAsync(500);
      expect(scheduler.listSchedules()[0].status).toBe('pending');

      // Fast forward another 500ms - task should execute
      await vi.advanceTimersByTimeAsync(500);
      expect(scheduler.listSchedules()[0].status).toBe('completed');
      vi.useRealTimers();
    });

    it('should schedule recurring periodic execution', async () => {
      vi.useFakeTimers();
      const req: CommandExecutionRequest = { commandId: 'test_cmd', args: { val: 'recurring' } };

      const schedCmd = await scheduler.scheduleRecurring(req, 1000);
      expect(schedCmd.status).toBe('pending');

      // Advance by 1000ms -> 1st run
      await vi.advanceTimersByTimeAsync(1000);
      expect(scheduler.listSchedules()[0].runCount).toBe(1);

      // Advance by another 1000ms -> 2nd run
      await vi.advanceTimersByTimeAsync(1000);
      expect(scheduler.listSchedules()[0].runCount).toBe(2);

      scheduler.cancelScheduled(schedCmd.scheduleId);
      vi.useRealTimers();
    });

    it('should support schedule cancellation', async () => {
      vi.useFakeTimers();
      const req: CommandExecutionRequest = { commandId: 'test_cmd' };

      const schedCmd = await scheduler.scheduleDelayed(req, 1000);
      expect(schedCmd.status).toBe('pending');

      const cancelled = scheduler.cancelScheduled(schedCmd.scheduleId);
      expect(cancelled).toBe(true);
      expect(scheduler.listSchedules()[0].status).toBe('cancelled');

      // Advance time - should not run
      await vi.advanceTimersByTimeAsync(1000);
      expect(scheduler.listSchedules()[0].runCount).toBe(0);
      vi.useRealTimers();
    });

    it('should support pause and resume scheduling', async () => {
      vi.useFakeTimers();
      const req: CommandExecutionRequest = { commandId: 'test_cmd' };

      scheduler.pauseSchedule();
      await scheduler.schedule(req);

      // Fast-forward - task should NOT execute because scheduler is paused
      await vi.runOnlyPendingTimersAsync();
      expect(scheduler.listSchedules()[0].status).toBe('pending');

      scheduler.resumeSchedule();
      // Re-trigger running the task in the next tick
      await vi.runOnlyPendingTimersAsync();
      expect(scheduler.listSchedules()[0].status).toBe('completed');
      vi.useRealTimers();
    });
  });

  describe('3. Command Queue Engine', () => {
    it('should enqueue and dequeue tasks in priority order', async () => {
      const req1: CommandExecutionRequest = { commandId: 'test_cmd', args: { id: 1 } };
      const req2: CommandExecutionRequest = { commandId: 'test_cmd', args: { id: 2 } };
      const req3: CommandExecutionRequest = { commandId: 'test_cmd', args: { id: 3 } };

      await queue.queue(req1, 10); // Priority 10
      await queue.queue(req2, 20); // Priority 20
      await queue.queue(req3, 5);  // Priority 5

      expect(queue.queueSize()).toBe(3);

      const first = await queue.dequeue();
      expect(first?.request.args?.id).toBe(2); // Higher priority dequeued first

      const second = await queue.dequeue();
      expect(second?.request.args?.id).toBe(1);

      const third = await queue.dequeue();
      expect(third?.request.args?.id).toBe(3);
    });

    it('should fallback to FIFO order for identical priorities', async () => {
      const req1: CommandExecutionRequest = { commandId: 'test_cmd', args: { id: 1 } };
      const req2: CommandExecutionRequest = { commandId: 'test_cmd', args: { id: 2 } };

      await queue.queue(req1, 10);
      await queue.queue(req2, 10);

      const first = await queue.dequeue();
      expect(first?.request.args?.id).toBe(1);

      const second = await queue.dequeue();
      expect(second?.request.args?.id).toBe(2);
    });

    it('should throw validation exception on queue overflow', async () => {
      const req: CommandExecutionRequest = { commandId: 'test_cmd' };
      for (let i = 0; i < 10; i++) {
        await queue.queue(req);
      }
      expect(queue.queueSize()).toBe(10);

      await expect(queue.queue(req)).rejects.toThrow('overflow');
    });

    it('should peek and clear queue', async () => {
      const req: CommandExecutionRequest = { commandId: 'test_cmd', args: { val: 42 } };
      await queue.queue(req);

      const entry = queue.peek();
      expect(entry?.request.args?.val).toBe(42);
      expect(queue.queueSize()).toBe(1);

      queue.clearQueue();
      expect(queue.queueSize()).toBe(0);
      expect(queue.peek()).toBeUndefined();
    });
  });

  describe('4. Background Execution Manager Engine', () => {
    it('should manage background task lifecycle from pending to completed', async () => {
      vi.useFakeTimers();
      const req: CommandExecutionRequest = { commandId: 'test_cmd', args: { val: 'bg' } };

      const task = await bgManager.submitBackgroundTask(req);
      expect(task.status).toBe('pending');
      expect(bgManager.statistics().totalSubmitted).toBe(1);

      await vi.runOnlyPendingTimersAsync();

      const list = bgManager.backgroundTasks();
      expect(list[0].status).toBe('completed');
      expect(bgManager.statistics().completedTasks).toBe(1);
      vi.useRealTimers();
    });

    it('should support background task cancellation', async () => {
      vi.useFakeTimers();
      const req: CommandExecutionRequest = { commandId: 'test_cmd' };

      const task = await bgManager.submitBackgroundTask(req);
      expect(task.status).toBe('pending');

      const cancelled = bgManager.cancelBackgroundTask(task.taskId);
      expect(cancelled).toBe(true);
      expect(bgManager.backgroundTasks()[0].status).toBe('cancelled');

      await vi.runOnlyPendingTimersAsync();
      expect(bgManager.statistics().completedTasks).toBe(0);
      expect(bgManager.statistics().cancelledTasks).toBe(1);
      vi.useRealTimers();
    });

    it('should perform exponential backoff retry scheduling on execution failures', async () => {
      vi.useFakeTimers();
      // Drop DB command is not registered, so validation fails, prompting retry
      const req: CommandExecutionRequest = { commandId: 'drop_database' };

      const task = await bgManager.submitBackgroundTask(req);
      expect(task.status).toBe('pending');

      // 1st attempt: runs execution, throws or fails, schedules retry 1
      await vi.runOnlyPendingTimersAsync();
      expect(bgManager.backgroundTasks()[0].retries).toBe(1);
      expect(bgManager.statistics().retryAttempts).toBe(1);

      // 2nd attempt: runs execution, fails, schedules retry 2
      await vi.runOnlyPendingTimersAsync();
      expect(bgManager.backgroundTasks()[0].retries).toBe(2);
      expect(bgManager.statistics().retryAttempts).toBe(2);

      // 3rd attempt: runs execution, fails, schedules retry 3
      await vi.runOnlyPendingTimersAsync();
      expect(bgManager.backgroundTasks()[0].retries).toBe(3);
      expect(bgManager.statistics().retryAttempts).toBe(3);

      // 4th attempt: max retries reached, marks task as failed
      await vi.runOnlyPendingTimersAsync();
      expect(bgManager.backgroundTasks()[0].status).toBe('failed');
      expect(bgManager.statistics().failedTasks).toBe(1);
      vi.useRealTimers();
    });
  });

  describe('5. Provider & Runtime Delegation Integration', () => {
    it('should delegate schedule, queue, and background tasks through CommandProvider and CommandRuntime', async () => {
      vi.useFakeTimers();
      const provider = new CommandProvider();
      provider.initialize();
      const runtime = new CommandRuntime(provider);

      runtime.registerCommand({ id: 'rt_cmd', displayName: 'Runtime Cmd' });
      runtime.registerHandler('rt_cmd', () => 'ok');

      const req: CommandExecutionRequest = { commandId: 'rt_cmd' };

      // Scheduler delegation
      const sched = await runtime.scheduleDelayed(req, 1000);
      expect(sched.scheduleId).toBeDefined();
      expect(runtime.listSchedules().length).toBe(1);
      runtime.cancelScheduled(sched.scheduleId);

      // Queue delegation
      const qEntry = await runtime.queue(req, 10);
      expect(qEntry.queueId).toBeDefined();
      expect(runtime.queueSize()).toBe(1);
      const dequeued = await runtime.dequeue();
      expect(dequeued?.queueId).toBe(qEntry.queueId);

      // Background delegation
      const bgTask = await runtime.submitBackgroundTask(req);
      expect(bgTask.taskId).toBeDefined();
      expect(runtime.backgroundTasks().length).toBe(1);
      runtime.cancelBackgroundTask(bgTask.taskId);

      vi.useRealTimers();
    });

    it('should aggregate scheduling, queue, and background execution diagnostics metrics', async () => {
      const runtime = getCommandRuntime();
      runtime.initialize();

      const diag = runtime.diagnostics();
      expect(diag.schedulingDiagnostics).toBeDefined();
      expect(diag.queueDiagnostics).toBeDefined();
      expect(diag.backgroundDiagnostics).toBeDefined();
    });
  });
});
