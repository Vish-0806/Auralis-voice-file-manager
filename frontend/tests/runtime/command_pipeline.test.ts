import { beforeEach, describe, expect, it } from 'vitest';
import {
  CommandExecutionStatus,
  CommandExecutor,
  CommandPipeline,
  CommandProvider,
  CommandRegistry,
  CommandRuntime,
  InterceptorManager,
  MiddlewareManager,
  MiddlewarePriority,
  createCommandMiddleware,
  createInterceptorRegistration,
  createMiddlewareExecution,
  createMiddlewareHealth,
  createMiddlewareResult,
  createMiddlewareStatistics,
  createPipelineCapabilities,
  createPipelineConfiguration,
  createPipelineDiagnostics,
  createPipelineExecution,
  createPipelineHealth,
  createPipelineSnapshot,
  createPipelineStatistics,
  getCommandRuntime,
  resetCommandProvider,
  resetCommandRuntime,
} from '../../src/runtime/commands';

describe('Phase 16.6.4 — Frontend Command Pipeline, Middleware & Interceptor Engine', () => {
  let registry: CommandRegistry;
  let executor: CommandExecutor;
  let middlewareManager: MiddlewareManager;
  let interceptorManager: InterceptorManager;
  let pipeline: CommandPipeline;

  beforeEach(() => {
    resetCommandRuntime();
    resetCommandProvider();

    registry = new CommandRegistry();
    executor = new CommandExecutor(registry);
    middlewareManager = new MiddlewareManager();
    interceptorManager = new InterceptorManager();
    pipeline = new CommandPipeline(executor, middlewareManager, interceptorManager);
  });

  describe('1. Immutable Pipeline Domain Models & Factory Functions', () => {
    it('should create immutable CommandMiddleware model', () => {
      const mw = createCommandMiddleware({
        name: 'Logger',
        phase: 'BEFORE',
        priority: MiddlewarePriority.HIGH,
        execute: () => {},
      });

      expect(mw.name).toBe('Logger');
      expect(mw.phase).toBe('BEFORE');
      expect(mw.priority).toBe(MiddlewarePriority.HIGH);
      expect(mw.enabled).toBe(true);
      expect(mw.middlewareId).toBeDefined();
      expect(Object.isFrozen(mw)).toBe(true);
    });

    it('should create immutable MiddlewareExecution model', () => {
      const exec = createMiddlewareExecution({
        middlewareId: 'mw_1',
        name: 'AuthCheck',
        phase: 'BEFORE',
        durationMs: 5,
      });

      expect(exec.middlewareId).toBe('mw_1');
      expect(exec.name).toBe('AuthCheck');
      expect(exec.durationMs).toBe(5);
      expect(exec.success).toBe(true);
      expect(Object.isFrozen(exec)).toBe(true);
    });

    it('should create immutable MiddlewareResult model', () => {
      const res = createMiddlewareResult({ totalExecutions: 3 });
      expect(res.totalExecutions).toBe(3);
      expect(res.executions).toEqual([]);
      expect(Object.isFrozen(res)).toBe(true);
    });

    it('should create immutable MiddlewareStatistics model', () => {
      const stats = createMiddlewareStatistics({ beforeCount: 2, afterCount: 1 });
      expect(stats.beforeCount).toBe(2);
      expect(stats.afterCount).toBe(1);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable MiddlewareHealth model', () => {
      const health = createMiddlewareHealth({ healthy: true });
      expect(health.healthy).toBe(true);
      expect(health.message).toBeDefined();
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable InterceptorRegistration model', () => {
      const int = createInterceptorRegistration({
        name: 'RetryInterceptor',
        priority: MiddlewarePriority.CRITICAL,
        intercept: async (_ctx, next) => next(),
      });

      expect(int.name).toBe('RetryInterceptor');
      expect(int.priority).toBe(MiddlewarePriority.CRITICAL);
      expect(int.interceptorId).toBeDefined();
      expect(Object.isFrozen(int)).toBe(true);
    });

    it('should create immutable PipelineExecution model', () => {
      const execRes = {
        executionId: 'e1',
        commandId: 'c1',
        status: CommandExecutionStatus.COMPLETED,
        warnings: [],
        timing: { startTime: '', durationMs: 0 },
        context: {} as any,
      };

      const pipeExec = createPipelineExecution({
        commandId: 'c1',
        executionResult: execRes,
        middlewareResult: createMiddlewareResult(),
      });

      expect(pipeExec.commandId).toBe('c1');
      expect(pipeExec.pipelineId).toBeDefined();
      expect(Object.isFrozen(pipeExec)).toBe(true);
    });

    it('should create immutable PipelineStatistics model', () => {
      const stats = createPipelineStatistics({ pipelineExecutions: 5 });
      expect(stats.pipelineExecutions).toBe(5);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable PipelineHealth model', () => {
      const health = createPipelineHealth({ healthy: true });
      expect(health.healthy).toBe(true);
      expect(health.message).toBeDefined();
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable PipelineConfiguration model', () => {
      const config = createPipelineConfiguration({ enableInterceptors: false });
      expect(config.enableInterceptors).toBe(false);
      expect(config.enableBeforeMiddleware).toBe(true);
      expect(Object.isFrozen(config)).toBe(true);
    });

    it('should create immutable PipelineCapabilities model', () => {
      const caps = createPipelineCapabilities();
      expect(caps.supportsBeforeMiddleware).toBe(true);
      expect(caps.supportsInterceptors).toBe(true);
      expect(Object.isFrozen(caps)).toBe(true);
    });

    it('should create immutable PipelineDiagnostics model', () => {
      const diag = createPipelineDiagnostics({
        statistics: createPipelineStatistics(),
        health: createPipelineHealth(),
      });

      expect(diag.statistics).toBeDefined();
      expect(diag.health).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });

    it('should create immutable PipelineSnapshot model', () => {
      const snap = createPipelineSnapshot();
      expect(snap.middleware).toEqual([]);
      expect(snap.interceptors).toEqual([]);
      expect(Object.isFrozen(snap)).toBe(true);
    });
  });

  describe('2. Middleware Registration & Priority Ordering', () => {
    it('should register before, after, and exception middleware', () => {
      const mwBefore = pipeline.registerMiddleware({
        name: 'PreMw',
        phase: 'BEFORE',
        execute: () => {},
      });

      const mwAfter = pipeline.registerMiddleware({
        name: 'PostMw',
        phase: 'AFTER',
        execute: () => {},
      });

      const mwException = pipeline.registerMiddleware({
        name: 'ErrMw',
        phase: 'EXCEPTION',
        execute: () => {},
      });

      expect(pipeline.listMiddlewares('BEFORE').length).toBe(1);
      expect(pipeline.listMiddlewares('AFTER').length).toBe(1);
      expect(pipeline.listMiddlewares('EXCEPTION').length).toBe(1);
      expect(mwBefore.middlewareId).toBeDefined();
      expect(mwAfter.middlewareId).toBeDefined();
      expect(mwException.middlewareId).toBeDefined();
    });

    it('should sort listMiddlewares by priority in descending order', () => {
      pipeline.registerMiddleware({
        name: 'LowMw',
        phase: 'BEFORE',
        priority: MiddlewarePriority.LOW,
        execute: () => {},
      });

      pipeline.registerMiddleware({
        name: 'CriticalMw',
        phase: 'BEFORE',
        priority: MiddlewarePriority.CRITICAL,
        execute: () => {},
      });

      pipeline.registerMiddleware({
        name: 'NormalMw',
        phase: 'BEFORE',
        priority: MiddlewarePriority.NORMAL,
        execute: () => {},
      });

      const list = pipeline.listMiddlewares('BEFORE');
      expect(list[0].name).toBe('CriticalMw');
      expect(list[1].name).toBe('NormalMw');
      expect(list[2].name).toBe('LowMw');
    });

    it('should remove middleware by ID', () => {
      const mw = pipeline.registerMiddleware({
        name: 'TempMw',
        execute: () => {},
      });

      expect(pipeline.listMiddlewares().length).toBe(1);
      const removed = pipeline.removeMiddleware(mw.middlewareId);
      expect(removed).toBe(true);
      expect(pipeline.listMiddlewares().length).toBe(0);
    });
  });

  describe('3. Interceptor Registration & Ordering', () => {
    it('should register and remove execution interceptors', () => {
      const interceptor = pipeline.registerInterceptor({
        name: 'TimingInterceptor',
        priority: MiddlewarePriority.HIGH,
        intercept: async (_ctx, next) => next(),
      });

      expect(pipeline.listInterceptors().length).toBe(1);
      expect(interceptor.interceptorId).toBeDefined();

      const removed = pipeline.removeInterceptor(interceptor.interceptorId);
      expect(removed).toBe(true);
      expect(pipeline.listInterceptors().length).toBe(0);
    });

    it('should list interceptors sorted by priority descending', () => {
      pipeline.registerInterceptor({
        name: 'NormalInt',
        priority: MiddlewarePriority.NORMAL,
        intercept: async (_ctx, next) => next(),
      });

      pipeline.registerInterceptor({
        name: 'CriticalInt',
        priority: MiddlewarePriority.CRITICAL,
        intercept: async (_ctx, next) => next(),
      });

      const list = pipeline.listInterceptors();
      expect(list[0].name).toBe('CriticalInt');
      expect(list[1].name).toBe('NormalInt');
    });
  });

  describe('4. Pipeline Execution Flow & Context Enrichment', () => {
    beforeEach(() => {
      registry.registerCommand({
        id: 'greet_user',
        displayName: 'Greet User',
      });

      executor.registerHandler('greet_user', (args: any) => `Hello ${args.name}`);
    });

    it('should execute before and after middleware around command execution', async () => {
      const executionOrder: string[] = [];

      pipeline.registerMiddleware({
        name: 'PreExecutionLog',
        phase: 'BEFORE',
        priority: MiddlewarePriority.HIGH,
        execute: () => {
          executionOrder.push('BEFORE_1');
        },
      });

      pipeline.registerMiddleware({
        name: 'PostExecutionLog',
        phase: 'AFTER',
        priority: MiddlewarePriority.HIGH,
        execute: () => {
          executionOrder.push('AFTER_1');
        },
      });

      const pipelineResult = await pipeline.executePipeline<string>({
        commandId: 'greet_user',
        args: { name: 'Alice' },
      });

      expect(pipelineResult.executionResult.value).toBe('Hello Alice');
      expect(executionOrder).toEqual(['BEFORE_1', 'AFTER_1']);
      expect(pipelineResult.middlewareResult.executions.length).toBe(2);
    });

    it('should wrap execution using interceptor chain in priority order', async () => {
      const trace: string[] = [];

      pipeline.registerInterceptor({
        name: 'OuterInterceptor',
        priority: MiddlewarePriority.HIGH,
        intercept: async (_ctx, next) => {
          trace.push('OUTER_START');
          const res = await next();
          trace.push('OUTER_END');
          return res;
        },
      });

      pipeline.registerInterceptor({
        name: 'InnerInterceptor',
        priority: MiddlewarePriority.NORMAL,
        intercept: async (_ctx, next) => {
          trace.push('INNER_START');
          const res = await next();
          trace.push('INNER_END');
          return res;
        },
      });

      const pipelineResult = await pipeline.executePipeline<string>({
        commandId: 'greet_user',
        args: { name: 'Bob' },
      });

      expect(pipelineResult.executionResult.value).toBe('Hello Bob');
      expect(trace).toEqual(['OUTER_START', 'INNER_START', 'INNER_END', 'OUTER_END']);
      expect(pipelineResult.interceptorResult?.totalInterceptors).toBe(2);
    });

    it('should invoke EXCEPTION middleware when execution throws an error', async () => {
      registry.registerCommand({ id: 'err_cmd', displayName: 'Failing Command' });
      executor.registerHandler('err_cmd', () => {
        throw new Error('Boom!');
      });

      let exceptionCaught = false;

      pipeline.registerMiddleware({
        name: 'ErrorLogger',
        phase: 'EXCEPTION',
        execute: (_ctx, _res, err) => {
          if (err?.message === 'Boom!') {
            exceptionCaught = true;
          }
        },
      });

      const pipelineResult = await pipeline.executePipeline({ commandId: 'err_cmd' });

      expect(pipelineResult.executionResult.status).toBe(CommandExecutionStatus.FAILED);
      expect(exceptionCaught).toBe(true);
    });
  });

  describe('5. Telemetry Statistics & Health', () => {
    beforeEach(() => {
      registry.registerCommand({ id: 'cmd_1', displayName: 'Cmd 1' });
      executor.registerHandler('cmd_1', () => true);
    });

    it('should generate PipelineStatistics snapshot', async () => {
      pipeline.registerMiddleware({ name: 'mw', phase: 'BEFORE', execute: () => {} });
      pipeline.registerInterceptor({ name: 'int', intercept: async (_ctx, next) => next() });

      await pipeline.executePipeline({ commandId: 'cmd_1' });

      const stats = pipeline.statistics();
      expect(stats.pipelineExecutions).toBe(1);
      expect(stats.middlewareExecutions).toBe(1);
      expect(stats.interceptorExecutions).toBe(1);
      expect(stats.pipelineFailures).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should generate PipelineHealth snapshot', async () => {
      await pipeline.executePipeline({ commandId: 'cmd_1' });

      const health = pipeline.health();
      expect(health.healthy).toBe(true);
      expect(health.failureRate).toBe(0);
      expect(health.message).toBeDefined();
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should generate PipelineDiagnostics snapshot', () => {
      const diag = pipeline.diagnostics();
      expect(diag.statistics).toBeDefined();
      expect(diag.health).toBeDefined();
      expect(diag.capabilities).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });

    it('should generate PipelineSnapshot snapshot', () => {
      pipeline.registerMiddleware({ name: 'mw1', execute: () => {} });
      const snap = pipeline.snapshot();

      expect(snap.middleware.length).toBe(1);
      expect(snap.timestamp).toBeDefined();
      expect(Object.isFrozen(snap)).toBe(true);
    });
  });

  describe('6. Provider & Runtime Delegation Integration', () => {
    it('should delegate middleware, interceptor, and pipeline execution through CommandProvider and CommandRuntime', async () => {
      const provider = new CommandProvider();
      provider.initialize();
      const runtime = new CommandRuntime(provider);

      runtime.registerCommand({ id: 'pipeline_cmd', displayName: 'Pipeline Cmd' });
      runtime.registerHandler('pipeline_cmd', (args: any) => args.val * 2);

      const mwLogs: string[] = [];
      runtime.registerMiddleware({
        name: 'ProviderMw',
        phase: 'BEFORE',
        execute: () => {
          mwLogs.push('MW_RAN');
        },
      });

      runtime.registerInterceptor({
        name: 'ProviderInt',
        intercept: async (_ctx, next) => {
          mwLogs.push('INT_BEFORE');
          const res = await next();
          mwLogs.push('INT_AFTER');
          return res;
        },
      });

      const pipeRes = await runtime.executePipeline<number>({
        commandId: 'pipeline_cmd',
        args: { val: 21 },
      });

      expect(pipeRes.executionResult.value).toBe(42);
      expect(mwLogs).toEqual(['MW_RAN', 'INT_BEFORE', 'INT_AFTER']);
      expect(runtime.pipelineStatistics().pipelineExecutions).toBe(1);
      expect(runtime.pipelineHealth().healthy).toBe(true);
    });

    it('should include pipeline diagnostics in runtime diagnostics()', async () => {
      const runtime = getCommandRuntime();
      runtime.initialize();

      runtime.registerCommand({ id: 'cmd_diag', displayName: 'Diag Cmd' });
      runtime.registerHandler('cmd_diag', () => 'ok');

      await runtime.executePipeline({ commandId: 'cmd_diag' });

      const diag = runtime.diagnostics();
      expect(diag.pipelineStatistics?.pipelineExecutions).toBe(1);
      expect(diag.pipelineHealth?.healthy).toBe(true);
      expect(diag.middlewareCount).toBeDefined();
      expect(diag.interceptorCount).toBeDefined();
    });
  });
});
