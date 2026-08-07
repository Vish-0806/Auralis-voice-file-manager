/**
 * Command Pipeline Implementation (Phase 16.6.6).
 *
 * Implements ICommandPipeline orchestrating CommandValidator, PermissionManager,
 * PolicyManager, CommandScheduler, CommandQueue, BackgroundExecutionManager,
 * MiddlewareManager, InterceptorManager, and CommandExecutor into a unified,
 * high-performance execution pipeline with validation, permissions, policy enforcement,
 * scheduling, priority queueing, background manager routing, pre/post-processing,
 * exception isolation, context enrichment, telemetry statistics, and health reporting.
 */

import {
  CommandExecutionRequest,
  CommandExecutionResult,
  CommandExecutionStatus,
  CommandMiddleware,
  InterceptorHandler,
  InterceptorRegistration,
  MiddlewareResult,
  PipelineConfiguration,
  PipelineDiagnostics,
  PipelineExecution,
  PipelineHealth,
  PipelineSnapshot,
  PipelineStatistics,
  createCommandExecutionContext,
  createCommandExecutionResult,
  createExecutionError,
  createExecutionTiming,
  createMiddlewareResult,
  createPipelineCapabilities,
  createPipelineConfiguration,
  createPipelineDiagnostics,
  createPipelineExecution,
  createPipelineHealth,
  createPipelineSnapshot,
  createPipelineStatistics,
} from './models';
import {
  ICommandExecutor,
  ICommandPipeline,
  ICommandRegistry,
  ICommandValidator,
  IInterceptorManager,
  IMiddlewareManager,
  IPermissionManager,
  IPolicyManager,
  ICommandScheduler,
  ICommandQueue,
  IBackgroundExecutionManager,
} from './interfaces';
import { CommandRegistry } from './command_registry';
import { CommandExecutor } from './command_executor';
import { MiddlewareManager } from './middleware_manager';
import { InterceptorManager } from './interceptor_manager';
import { CommandValidator } from './command_validator';
import { PermissionManager } from './permission_manager';
import { PolicyManager } from './policy_manager';
import { CommandScheduler } from './command_scheduler';
import { CommandQueue } from './command_queue';
import { BackgroundExecutionManager } from './background_execution_manager';

export class CommandPipeline implements ICommandPipeline {
  private readonly _registry: ICommandRegistry;
  private readonly _executor: ICommandExecutor;
  private readonly _middlewareManager: IMiddlewareManager;
  private readonly _interceptorManager: IInterceptorManager;
  private readonly _validator: ICommandValidator;
  private readonly _permissionManager: IPermissionManager;
  private readonly _policyManager: IPolicyManager;
  private readonly _scheduler: ICommandScheduler;
  private readonly _queue: ICommandQueue;
  private readonly _backgroundExecutionManager: IBackgroundExecutionManager;
  private readonly _config: PipelineConfiguration;

  private _pipelineExecutions = 0;
  private _pipelineFailures = 0;
  private _activePipelines = 0;
  private _pipelineTimes: number[] = [];

  constructor(
    executor?: ICommandExecutor,
    middlewareManager?: IMiddlewareManager,
    interceptorManager?: IInterceptorManager,
    config?: PipelineConfiguration,
    registry?: ICommandRegistry,
    validator?: ICommandValidator,
    permissionManager?: IPermissionManager,
    policyManager?: IPolicyManager,
    scheduler?: ICommandScheduler,
    queue?: ICommandQueue,
    backgroundExecutionManager?: IBackgroundExecutionManager,
  ) {
    this._registry = registry ?? new CommandRegistry();
    this._executor = executor ?? new CommandExecutor(this._registry);
    this._middlewareManager = middlewareManager ?? new MiddlewareManager();
    this._interceptorManager = interceptorManager ?? new InterceptorManager();
    this._validator = validator ?? new CommandValidator(this._registry);
    this._permissionManager = permissionManager ?? new PermissionManager();
    this._policyManager = policyManager ?? new PolicyManager();
    this._scheduler = scheduler ?? new CommandScheduler(this);
    this._queue = queue ?? new CommandQueue();
    this._backgroundExecutionManager = backgroundExecutionManager ?? new BackgroundExecutionManager(this);
    this._config = config ?? createPipelineConfiguration();
  }

  public registerMiddleware(middleware: Parameters<IMiddlewareManager['registerMiddleware']>[0]): CommandMiddleware {
    return this._middlewareManager.registerMiddleware(middleware);
  }

  public removeMiddleware(middlewareId: string): boolean {
    return this._middlewareManager.removeMiddleware(middlewareId);
  }

  public listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware> {
    return this._middlewareManager.listMiddlewares(phase);
  }

  public registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult> {
    return this._interceptorManager.registerInterceptor<TResult>(interceptor);
  }

  public removeInterceptor(interceptorId: string): boolean {
    return this._interceptorManager.removeInterceptor(interceptorId);
  }

  public listInterceptors(): ReadonlyArray<InterceptorRegistration> {
    return this._interceptorManager.listInterceptors();
  }

  public async executePipeline<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<PipelineExecution<TResult>> {
    this._pipelineExecutions++;
    this._activePipelines++;
    const startPerf = performance ? performance.now() : Date.now();
    const startTime = new Date().toISOString();

    const context = createCommandExecutionContext({
      commandId: request?.commandId ?? 'unknown',
      mode: 'async',
      args: request?.args ?? {},
      source: request?.source,
      userId: request?.userId,
      sessionId: request?.sessionId,
      correlationId: request?.correlationId,
      metadata: request?.metadata,
    });

    // 1. Validation Stage
    const validationResult = await this._validator.validate(request);
    if (!validationResult.valid) {
      this._pipelineFailures++;
      this._activePipelines = Math.max(0, this._activePipelines - 1);
      const endPerf = performance ? performance.now() : Date.now();

      const firstError = validationResult.issues.find((i) => i.severity === 'error');
      const timing = createExecutionTiming({
        startTime,
        endTime: new Date().toISOString(),
        durationMs: Math.max(0, Math.round((endPerf - startPerf) * 100) / 100),
      });

      const execResult = createCommandExecutionResult<TResult>({
        commandId: request?.commandId ?? 'unknown',
        status: CommandExecutionStatus.VALIDATION_FAILED,
        error: createExecutionError({
          code: firstError?.code ?? 'VALIDATION_FAILED',
          message: firstError?.message ?? 'Command validation failed.',
        }),
        timing,
        context,
      });

      return createPipelineExecution<TResult>({
        commandId: request?.commandId ?? 'unknown',
        executionResult: execResult,
        middlewareResult: createMiddlewareResult(),
        durationMs: timing.durationMs,
      });
    }

    // 2. Permission Check Stage
    const definition = this._registry.findCommand(request.commandId) ?? this._registry.findByAlias(request.commandId);
    if (definition && definition.permission) {
      const subject = request.userId ?? 'anonymous';
      const permResult = this._permissionManager.hasPermission(subject, definition.permission);
      if (!permResult.granted) {
        this._pipelineFailures++;
        this._activePipelines = Math.max(0, this._activePipelines - 1);
        const endPerf = performance ? performance.now() : Date.now();

        const timing = createExecutionTiming({
          startTime,
          endTime: new Date().toISOString(),
          durationMs: Math.max(0, Math.round((endPerf - startPerf) * 100) / 100),
        });

        const execResult = createCommandExecutionResult<TResult>({
          commandId: definition.id,
          status: CommandExecutionStatus.REJECTED,
          error: createExecutionError({
            code: 'PERMISSION_DENIED',
            message: permResult.reason ?? `Permission '${definition.permission}' denied for user '${subject}'.`,
          }),
          timing,
          context,
        });

        return createPipelineExecution<TResult>({
          commandId: definition.id,
          executionResult: execResult,
          middlewareResult: createMiddlewareResult(),
          durationMs: timing.durationMs,
        });
      }
    }

    // 3. Policy Evaluation Stage
    const policyDecision = await this._policyManager.evaluatePolicy(request, context);
    if (!policyDecision.allowed) {
      this._pipelineFailures++;
      this._activePipelines = Math.max(0, this._activePipelines - 1);
      const endPerf = performance ? performance.now() : Date.now();

      const timing = createExecutionTiming({
        startTime,
        endTime: new Date().toISOString(),
        durationMs: Math.max(0, Math.round((endPerf - startPerf) * 100) / 100),
      });

      const execResult = createCommandExecutionResult<TResult>({
        commandId: request?.commandId ?? 'unknown',
        status: CommandExecutionStatus.REJECTED,
        error: createExecutionError({
          code: 'POLICY_DENIED',
          message: policyDecision.reason ?? 'Command execution denied by policy.',
        }),
        timing,
        context,
      });

      return createPipelineExecution<TResult>({
        commandId: request?.commandId ?? 'unknown',
        executionResult: execResult,
        middlewareResult: createMiddlewareResult(),
        durationMs: timing.durationMs,
      });
    }

    // 4. Scheduler check
    const isScheduled = request.metadata?.schedule || request.metadata?.delayMs !== undefined || request.metadata?.intervalMs !== undefined;
    const isScheduledExecution = request.metadata?.isScheduledExecution;
    if (isScheduled && !isScheduledExecution) {
      const delayMs = typeof request.metadata?.delayMs === 'number' ? request.metadata.delayMs : undefined;
      const intervalMs = typeof request.metadata?.intervalMs === 'number' ? request.metadata.intervalMs : undefined;

      if (intervalMs !== undefined && intervalMs > 0) {
        await this._scheduler.scheduleRecurring(request, intervalMs);
      } else {
        await this._scheduler.schedule(request, delayMs);
      }

      this._activePipelines = Math.max(0, this._activePipelines - 1);
      const endPerf = performance ? performance.now() : Date.now();
      const timing = createExecutionTiming({
        startTime,
        endTime: new Date().toISOString(),
        durationMs: Math.max(0, Math.round((endPerf - startPerf) * 100) / 100),
      });

      const execResult = createCommandExecutionResult<TResult>({
        commandId: request.commandId,
        status: CommandExecutionStatus.PENDING,
        timing,
        context,
      });

      return createPipelineExecution<TResult>({
        commandId: request.commandId,
        executionResult: execResult,
        middlewareResult: createMiddlewareResult(),
        durationMs: timing.durationMs,
      });
    }

    // 5. Queue check
    const isQueued = request.metadata?.queue || request.metadata?.priority !== undefined;
    const isQueuedExecution = request.metadata?.isQueuedExecution;
    if (isQueued && !isQueuedExecution) {
      const priority = typeof request.metadata?.priority === 'number' ? request.metadata.priority : 0;
      await this._queue.queue(request, priority);

      this._activePipelines = Math.max(0, this._activePipelines - 1);
      const endPerf = performance ? performance.now() : Date.now();
      const timing = createExecutionTiming({
        startTime,
        endTime: new Date().toISOString(),
        durationMs: Math.max(0, Math.round((endPerf - startPerf) * 100) / 100),
      });

      const execResult = createCommandExecutionResult<TResult>({
        commandId: request.commandId,
        status: CommandExecutionStatus.PENDING,
        timing,
        context,
      });

      return createPipelineExecution<TResult>({
        commandId: request.commandId,
        executionResult: execResult,
        middlewareResult: createMiddlewareResult(),
        durationMs: timing.durationMs,
      });
    }

    // 6. Background Manager check
    const isBackground = request.metadata?.background;
    const isBackgroundExecution = request.metadata?.isBackgroundExecution;
    if (isBackground && !isBackgroundExecution) {
      await this._backgroundExecutionManager.submitBackgroundTask(request);

      this._activePipelines = Math.max(0, this._activePipelines - 1);
      const endPerf = performance ? performance.now() : Date.now();
      const timing = createExecutionTiming({
        startTime,
        endTime: new Date().toISOString(),
        durationMs: Math.max(0, Math.round((endPerf - startPerf) * 100) / 100),
      });

      const execResult = createCommandExecutionResult<TResult>({
        commandId: request.commandId,
        status: CommandExecutionStatus.PENDING,
        timing,
        context,
      });

      return createPipelineExecution<TResult>({
        commandId: request.commandId,
        executionResult: execResult,
        middlewareResult: createMiddlewareResult(),
        durationMs: timing.durationMs,
      });
    }

    // 7. BEFORE Middleware Phase
    let beforeResult: MiddlewareResult = createMiddlewareResult();
    if (this._config.enableBeforeMiddleware) {
      beforeResult = await this._middlewareManager.executeBefore(context);
    }

    let executionResult: CommandExecutionResult<TResult>;
    let interceptorResult = undefined;

    try {
      // 8. Interceptor Chain & Executor Phase
      if (this._config.enableInterceptors) {
        const intRes = await this._interceptorManager.executeChain<TResult>(
          context,
          () => this._executor.executeAsync<TResult>(request),
        );
        interceptorResult = intRes;
        executionResult = intRes.executionResult;
      } else {
        executionResult = await this._executor.executeAsync<TResult>(request);
      }

      if (executionResult.status === CommandExecutionStatus.FAILED) {
        this._pipelineFailures++;
        if (this._config.enableExceptionMiddleware && executionResult.error) {
          await this._middlewareManager.executeException(
            context,
            new Error(executionResult.error.message),
          );
        }
      }
    } catch (err: any) {
      this._pipelineFailures++;
      if (this._config.enableExceptionMiddleware) {
        await this._middlewareManager.executeException(context, err);
      }

      const timing = createExecutionTiming({
        startTime,
        endTime: new Date().toISOString(),
        durationMs: 0,
      });

      const error = createExecutionError({
        code: 'PIPELINE_EXECUTION_ERROR',
        message: err?.message ?? 'Pipeline execution encountered an unhandled exception.',
        stack: err?.stack,
      });

      executionResult = createCommandExecutionResult<TResult>({
        commandId: request?.commandId ?? 'unknown',
        status: CommandExecutionStatus.FAILED,
        error,
        timing,
        context,
      });
    }

    // 9. AFTER Middleware Phase
    let afterResult: MiddlewareResult = createMiddlewareResult();
    if (this._config.enableAfterMiddleware) {
      afterResult = await this._middlewareManager.executeAfter(context, executionResult);
    }

    const endPerf = performance ? performance.now() : Date.now();
    const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
    this.recordPipelineTime(durationMs);
    this._activePipelines = Math.max(0, this._activePipelines - 1);

    const combinedExecutions = [
      ...beforeResult.executions,
      ...afterResult.executions,
    ];

    const middlewareResult = createMiddlewareResult({
      executions: combinedExecutions,
    });

    return createPipelineExecution<TResult>({
      commandId: request?.commandId ?? 'unknown',
      executionResult,
      middlewareResult,
      interceptorResult,
      durationMs,
    });
  }

  public statistics(): PipelineStatistics {
    const mwStats = this._middlewareManager.statistics();
    const times = this._pipelineTimes;
    const totalTimes = times.length;
    const avgTime = totalTimes > 0 ? times.reduce((a, b) => a + b, 0) / totalTimes : 0;
    const maxTime = totalTimes > 0 ? Math.max(...times) : 0;
    const minTime = totalTimes > 0 ? Math.min(...times) : 0;

    return createPipelineStatistics({
      middlewareExecutions: mwStats.totalExecutions,
      interceptorExecutions: this.listInterceptors().length,
      pipelineExecutions: this._pipelineExecutions,
      pipelineFailures: this._pipelineFailures,
      averagePipelineTime: Math.round(avgTime * 100) / 100,
      maximumPipelineTime: maxTime,
      minimumPipelineTime: minTime,
      activePipelines: this._activePipelines,
    });
  }

  public health(): PipelineHealth {
    const stats = this.statistics();
    const failureRate =
      stats.pipelineExecutions > 0
        ? Math.round((stats.pipelineFailures / stats.pipelineExecutions) * 100)
        : 0;
    const healthy = failureRate <= 10;

    return createPipelineHealth({
      healthy,
      failureRate,
      averagePipelineTime: stats.averagePipelineTime,
      registeredMiddleware: this._middlewareManager.listMiddlewares().length,
      registeredInterceptors: this._interceptorManager.listInterceptors().length,
      pipelineThroughput: stats.pipelineExecutions,
      message: healthy
        ? 'Command pipeline engine is operational.'
        : `Command pipeline engine elevated failure rate (${failureRate}%).`,
    });
  }

  public diagnostics(): PipelineDiagnostics {
    return createPipelineDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      capabilities: createPipelineCapabilities(),
      middlewareCount: this.listMiddlewares().length,
      interceptorCount: this.listInterceptors().length,
    });
  }

  public snapshot(): PipelineSnapshot {
    return createPipelineSnapshot({
      middleware: this.listMiddlewares(),
      interceptors: this.listInterceptors(),
    });
  }

  private recordPipelineTime(durationMs: number): void {
    this._pipelineTimes.push(durationMs);
    if (this._pipelineTimes.length > 1000) {
      this._pipelineTimes.shift();
    }
  }
}
