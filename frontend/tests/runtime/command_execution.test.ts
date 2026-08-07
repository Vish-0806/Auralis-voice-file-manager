import { beforeEach, describe, expect, it } from 'vitest';
import {
  CommandExecutionException,
  CommandExecutor,
  CommandExecutionStatus,
  CommandProvider,
  CommandRegistry,
  CommandRuntime,
  createCommandExecutionConfiguration,
  createCommandExecutionContext,
  createCommandExecutionRecord,
  createCommandExecutionRequest,
  createCommandExecutionResult,
  createCommandExecutionStatistics,
  createExecutionCapabilities,
  createExecutionDiagnostics,
  createExecutionError,
  createExecutionPipeline,
  createExecutionTiming,
  createExecutionWarning,
  getCommandRuntime,
  resetCommandProvider,
  resetCommandRuntime,
} from '../../src/runtime/commands';

describe('Phase 16.6.3 — Frontend Command Execution Engine', () => {
  let registry: CommandRegistry;
  let executor: CommandExecutor;

  beforeEach(() => {
    resetCommandRuntime();
    resetCommandProvider();
    registry = new CommandRegistry();
    executor = new CommandExecutor(registry);
  });

  describe('1. Immutable Execution Models & Factory Functions', () => {
    it('should create immutable ExecutionTiming model', () => {
      const timing = createExecutionTiming({ durationMs: 15 });
      expect(timing.durationMs).toBe(15);
      expect(timing.startTime).toBeDefined();
      expect(Object.isFrozen(timing)).toBe(true);
    });

    it('should create immutable ExecutionError model', () => {
      const error = createExecutionError({ code: 'ERR_1', message: 'Failed to run' });
      expect(error.code).toBe('ERR_1');
      expect(error.message).toBe('Failed to run');
      expect(Object.isFrozen(error)).toBe(true);
    });

    it('should create immutable ExecutionWarning model', () => {
      const warn = createExecutionWarning({ message: 'Deprecated API' });
      expect(warn.message).toBe('Deprecated API');
      expect(warn.timestamp).toBeDefined();
      expect(Object.isFrozen(warn)).toBe(true);
    });

    it('should create immutable CommandExecutionContext model', () => {
      const ctx = createCommandExecutionContext({
        commandId: 'cmd_open',
        mode: 'sync',
        args: { file: 'test.txt' },
      });

      expect(ctx.commandId).toBe('cmd_open');
      expect(ctx.mode).toBe('sync');
      expect(ctx.args).toEqual({ file: 'test.txt' });
      expect(ctx.executionId).toBeDefined();
      expect(Object.isFrozen(ctx)).toBe(true);
      expect(Object.isFrozen(ctx.args)).toBe(true);
    });

    it('should create immutable CommandExecutionRequest model', () => {
      const req = createCommandExecutionRequest({
        commandId: 'file_delete',
        args: { id: 123 },
      });

      expect(req.commandId).toBe('file_delete');
      expect(req.args).toEqual({ id: 123 });
      expect(Object.isFrozen(req)).toBe(true);
    });

    it('should create immutable CommandExecutionResult model', () => {
      const ctx = createCommandExecutionContext({ commandId: 'cmd_1' });
      const res = createCommandExecutionResult({
        commandId: 'cmd_1',
        context: ctx,
        value: { success: true },
      });

      expect(res.commandId).toBe('cmd_1');
      expect(res.status).toBe(CommandExecutionStatus.COMPLETED);
      expect(res.value).toEqual({ success: true });
      expect(Object.isFrozen(res)).toBe(true);
    });

    it('should create immutable CommandExecutionRecord model', () => {
      const ctx = createCommandExecutionContext({ commandId: 'c1' });
      const res = createCommandExecutionResult({ commandId: 'c1', context: ctx });
      const record = createCommandExecutionRecord({ result: res });

      expect(record.result.commandId).toBe('c1');
      expect(record.recordedAt).toBeDefined();
      expect(Object.isFrozen(record)).toBe(true);
    });

    it('should create immutable CommandExecutionStatistics model', () => {
      const stats = createCommandExecutionStatistics({ executions: 10, successfulExecutions: 8 });
      expect(stats.executions).toBe(10);
      expect(stats.successfulExecutions).toBe(8);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable CommandExecutionConfiguration model', () => {
      const cfg = createCommandExecutionConfiguration({ maxHistorySize: 500 });
      expect(cfg.maxHistorySize).toBe(500);
      expect(cfg.executionTimeoutMs).toBe(30000);
      expect(Object.isFrozen(cfg)).toBe(true);
    });

    it('should create immutable ExecutionPipeline model', () => {
      const pipe = createExecutionPipeline();
      expect(pipe.steps.length).toBeGreaterThan(0);
      expect(Object.isFrozen(pipe)).toBe(true);
    });

    it('should create immutable ExecutionCapabilities model', () => {
      const caps = createExecutionCapabilities();
      expect(caps.supportsSyncExecution).toBe(true);
      expect(caps.supportsAsyncExecution).toBe(true);
      expect(Object.isFrozen(caps)).toBe(true);
    });

    it('should create immutable ExecutionDiagnostics model', () => {
      const stats = createCommandExecutionStatistics();
      const health = executor.health();
      const diag = createExecutionDiagnostics({ statistics: stats, health });

      expect(diag.statistics).toBeDefined();
      expect(diag.health).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  describe('2. Synchronous Command Execution', () => {
    beforeEach(() => {
      registry.registerCommand({
        id: 'math_add',
        displayName: 'Add Numbers',
        category: 'Math',
      });
    });

    it('should execute synchronous handler and return COMPLETED result', () => {
      executor.registerHandler('math_add', (args: any) => args.a + args.b);

      const result = executor.execute<number>({
        commandId: 'math_add',
        args: { a: 5, b: 3 },
      });

      expect(result.status).toBe(CommandExecutionStatus.COMPLETED);
      expect(result.value).toBe(8);
      expect(result.timing.durationMs).toBeGreaterThanOrEqual(0);
      expect(result.error).toBeUndefined();
    });

    it('should pass execution context to synchronous handler', () => {
      let capturedCtx: any = null;

      executor.registerHandler('math_add', (_args: any, ctx: any) => {
        capturedCtx = ctx;
        return true;
      });

      executor.execute({
        commandId: 'math_add',
        userId: 'user_123',
        source: 'button_click',
      });

      expect(capturedCtx).toBeDefined();
      expect(capturedCtx.userId).toBe('user_123');
      expect(capturedCtx.source).toBe('button_click');
      expect(capturedCtx.mode).toBe('sync');
    });

    it('should handle thrown error in sync handler and return FAILED result', () => {
      executor.registerHandler('math_add', (_args: any) => {
        throw new Error('Sync handler exception');
      });

      const result = executor.execute({ commandId: 'math_add' });

      expect(result.status).toBe(CommandExecutionStatus.FAILED);
      expect(result.error?.message).toBe('Sync handler exception');
      expect(executor.statistics().failedExecutions).toBe(1);
    });

    it('should fail when async handler is called via execute()', () => {
      executor.registerHandler('math_add', async () => 42);

      const result = executor.execute({ commandId: 'math_add' });

      expect(result.status).toBe(CommandExecutionStatus.FAILED);
      expect(result.error?.code).toBe('SYNC_EXECUTION_ASYNC_HANDLER');
    });
  });

  describe('3. Asynchronous Command Execution', () => {
    beforeEach(() => {
      registry.registerCommand({
        id: 'fetch_data',
        displayName: 'Fetch Remote Data',
        category: 'Network',
      });
    });

    it('should execute async handler and await Promise result', async () => {
      executor.registerHandler('fetch_data', async (args: any) => {
        return { data: `Data for ${args.id}` };
      });

      const result = await executor.executeAsync<{ data: string }>({
        commandId: 'fetch_data',
        args: { id: 'item_99' },
      });

      expect(result.status).toBe(CommandExecutionStatus.COMPLETED);
      expect(result.value).toEqual({ data: 'Data for item_99' });
      expect(result.context.mode).toBe('async');
    });

    it('should handle rejected Promise in async handler and return FAILED result', async () => {
      executor.registerHandler('fetch_data', async () => {
        throw new Error('Network request failed');
      });

      const result = await executor.executeAsync({ commandId: 'fetch_data' });

      expect(result.status).toBe(CommandExecutionStatus.FAILED);
      expect(result.error?.message).toBe('Network request failed');
      expect(executor.statistics().failedExecutions).toBe(1);
    });
  });

  describe('4. Parameter Validation & Execution Pipeline', () => {
    beforeEach(() => {
      registry.registerCommand({
        id: 'create_user',
        displayName: 'Create User',
        parameters: [
          { name: 'username', type: 'string', required: true },
          { name: 'age', type: 'number', required: false },
          { name: 'isAdmin', type: 'boolean', required: false },
          { name: 'roles', type: 'array', required: false },
          { name: 'config', type: 'object', required: false },
        ],
      });

      executor.registerHandler('create_user', (args: any) => ({ created: true, ...args }));
    });

    it('should fail validation if required parameter is missing', () => {
      const result = executor.execute({
        commandId: 'create_user',
        args: { age: 30 },
      });

      expect(result.status).toBe(CommandExecutionStatus.VALIDATION_FAILED);
      expect(result.error?.code).toBe('MISSING_REQUIRED_PARAMETER');
      expect(executor.statistics().validationFailures).toBe(1);
    });

    it('should fail validation if parameter type is invalid', () => {
      const result = executor.execute({
        commandId: 'create_user',
        args: { username: 'alice', age: 'not_a_number' },
      });

      expect(result.status).toBe(CommandExecutionStatus.VALIDATION_FAILED);
      expect(result.error?.code).toBe('INVALID_PARAMETER_TYPE');
    });

    it('should pass validation when all types match correctly', () => {
      const result = executor.execute({
        commandId: 'create_user',
        args: {
          username: 'bob',
          age: 25,
          isAdmin: true,
          roles: ['admin', 'user'],
          config: { theme: 'dark' },
        },
      });

      expect(result.status).toBe(CommandExecutionStatus.COMPLETED);
    });

    it('should validate execution via validateExecution() without invoking handler', () => {
      let handlerCalled = false;
      executor.registerHandler('create_user', () => {
        handlerCalled = true;
      });

      const validation = executor.validateExecution({
        commandId: 'create_user',
        args: { username: 'charlie' },
      });

      expect(validation.value).toBe(true);
      expect(handlerCalled).toBe(false);
    });
  });

  describe('5. Command Lookup, Disabled Commands & Warnings', () => {
    it('should return REJECTED status for unregistered command', () => {
      const result = executor.execute({ commandId: 'unregistered_cmd' });
      expect(result.status).toBe(CommandExecutionStatus.REJECTED);
      expect(result.error?.code).toBe('UNKNOWN_COMMAND');
    });

    it('should return REJECTED status for disabled command', () => {
      registry.registerCommand({
        id: 'disabled_cmd',
        displayName: 'Disabled Command',
        enabled: false,
      });
      executor.registerHandler('disabled_cmd', () => true);

      const result = executor.execute({ commandId: 'disabled_cmd' });
      expect(result.status).toBe(CommandExecutionStatus.REJECTED);
      expect(result.error?.code).toBe('COMMAND_DISABLED');
    });

    it('should return VALIDATION_FAILED when no handler is registered', () => {
      registry.registerCommand({
        id: 'no_handler_cmd',
        displayName: 'No Handler Command',
      });

      const result = executor.execute({ commandId: 'no_handler_cmd' });
      expect(result.status).toBe(CommandExecutionStatus.VALIDATION_FAILED);
      expect(result.error?.code).toBe('MISSING_HANDLER');
    });

    it('should generate COMMAND_DEPRECATED warning for deprecated command', () => {
      registry.registerCommand({
        id: 'old_cmd',
        displayName: 'Deprecated Command',
        deprecated: true,
      });
      executor.registerHandler('old_cmd', () => 'legacy');

      const result = executor.execute({ commandId: 'old_cmd' });

      expect(result.status).toBe(CommandExecutionStatus.COMPLETED);
      expect(result.warnings.length).toBe(1);
      expect(result.warnings[0].code).toBe('COMMAND_DEPRECATED');
    });

    it('should allow execution via command alias', () => {
      registry.registerCommand({
        id: 'file_open',
        displayName: 'Open File',
        aliases: ['open'],
      });
      executor.registerHandler('file_open', () => 'file_contents');

      const result = executor.execute({ commandId: 'open' });
      expect(result.status).toBe(CommandExecutionStatus.COMPLETED);
      expect(result.value).toBe('file_contents');
    });
  });

  describe('6. Execution History & Bounded Retention', () => {
    beforeEach(() => {
      registry.registerCommand({ id: 'c1', displayName: 'C1' });
      executor.registerHandler('c1', () => true);
    });

    it('should record execution history records', () => {
      executor.execute({ commandId: 'c1' });
      executor.execute({ commandId: 'c1' });

      const history = executor.executionHistory();
      expect(history.length).toBe(2);
      expect(Object.isFrozen(history)).toBe(true);
    });

    it('should clear execution history on clearExecutionHistory()', () => {
      executor.execute({ commandId: 'c1' });
      executor.clearExecutionHistory();

      expect(executor.executionHistory().length).toBe(0);
    });

    it('should enforce maxHistorySize capacity retention', () => {
      const customConfig = createCommandExecutionConfiguration({ maxHistorySize: 3 });
      const smallExecutor = new CommandExecutor(registry, customConfig);
      smallExecutor.registerHandler('c1', () => true);

      for (let i = 0; i < 5; i++) {
        smallExecutor.execute({ commandId: 'c1' });
      }

      expect(smallExecutor.executionHistory().length).toBe(3);
    });
  });

  describe('7. Active Executions & Cancellation', () => {
    it('should handle cancelExecution() for unknown execution ID', () => {
      const cancelled = executor.cancelExecution('non_existent_exec_id');
      expect(cancelled).toBe(false);
    });

    it('should register and unregister handlers', () => {
      expect(executor.hasHandler('test_cmd')).toBe(false);
      executor.registerHandler('test_cmd', () => 1);
      expect(executor.hasHandler('test_cmd')).toBe(true);

      const unreg = executor.unregisterHandler('test_cmd');
      expect(unreg).toBe(true);
      expect(executor.hasHandler('test_cmd')).toBe(false);
    });

    it('should throw exception when registering empty commandId or null handler', () => {
      expect(() => executor.registerHandler('', () => {})).toThrow(CommandExecutionException);
      expect(() => executor.registerHandler('cmd', null as any)).toThrow(
        CommandExecutionException,
      );
    });
  });

  describe('8. Telemetry Statistics & Health', () => {
    beforeEach(() => {
      registry.registerCommand({ id: 'c1', displayName: 'C1' });
      executor.registerHandler('c1', () => 'ok');
    });

    it('should generate CommandExecutionStatistics snapshot', () => {
      executor.execute({ commandId: 'c1' });

      const stats = executor.statistics();
      expect(stats.executions).toBe(1);
      expect(stats.successfulExecutions).toBe(1);
      expect(stats.failedExecutions).toBe(0);
      expect(stats.historySize).toBe(1);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should generate healthy CommandExecutionHealth snapshot', () => {
      executor.execute({ commandId: 'c1' });

      const health = executor.health();
      expect(health.healthy).toBe(true);
      expect(health.successRate).toBe(100);
      expect(health.failureRate).toBe(0);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should generate ExecutionDiagnostics snapshot', () => {
      executor.execute({ commandId: 'c1' });

      const diag = executor.diagnostics();
      expect(diag.statistics.executions).toBe(1);
      expect(diag.health.healthy).toBe(true);
      expect(diag.historySize).toBe(1);
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  describe('9. Provider & Runtime Delegation Integration', () => {
    it('should delegate registerHandler, execute, and history through CommandProvider and CommandRuntime', async () => {
      const provider = new CommandProvider();
      provider.initialize();
      const runtime = new CommandRuntime(provider);

      runtime.registerCommand({
        id: 'calc_square',
        displayName: 'Calculate Square',
      });

      runtime.registerHandler('calc_square', (args: any) => args.n * args.n);
      expect(runtime.hasHandler('calc_square')).toBe(true);

      const syncResult = runtime.execute<number>({
        commandId: 'calc_square',
        args: { n: 4 },
      });
      expect(syncResult.value).toBe(16);

      runtime.registerCommand({
        id: 'async_greet',
        displayName: 'Async Greet',
      });
      runtime.registerHandler('async_greet', async (args: any) => `Hello ${args.name}`);

      const asyncResult = await runtime.executeAsync<string>({
        commandId: 'async_greet',
        args: { name: 'World' },
      });
      expect(asyncResult.value).toBe('Hello World');

      expect(runtime.executionHistory().length).toBe(2);
      expect(runtime.executionStatistics().executions).toBe(2);
      expect(runtime.executionHealth().healthy).toBe(true);
    });

    it('should include execution diagnostics in runtime diagnostics()', () => {
      const runtime = getCommandRuntime();
      runtime.initialize();

      runtime.registerCommand({ id: 'ping', displayName: 'Ping' });
      runtime.registerHandler('ping', () => 'pong');
      runtime.execute({ commandId: 'ping' });

      const diag = runtime.diagnostics();
      expect(diag.executionStatistics?.executions).toBe(1);
      expect(diag.executionHealth?.healthy).toBe(true);
      expect(diag.executionHistorySize).toBe(1);
    });
  });
});
