/**
 * Command Pipeline Implementation (Phase 16.6.4).
 *
 * Implements ICommandPipeline orchestrating MiddlewareManager, InterceptorManager,
 * and CommandExecutor into a unified, high-performance execution pipeline with pre/post-processing,
 * exception isolation, context enrichment, telemetry statistics, and health reporting.
 */

import {
  CommandExecutionContext,
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
  IInterceptorManager,
  IMiddlewareManager,
} from './interfaces';
import { CommandExecutor } from './command_executor';
import { MiddlewareManager } from './middleware_manager';
import { InterceptorManager } from './interceptor_manager';

export class CommandPipeline implements ICommandPipeline {
  private readonly _middlewareManager: IMiddlewareManager;
  private readonly _interceptorManager: IInterceptorManager;
  private readonly _executor: ICommandExecutor;
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
  ) {
    this._executor = executor ?? new CommandExecutor();
    this._middlewareManager = middlewareManager ?? new MiddlewareManager();
    this._interceptorManager = interceptorManager ?? new InterceptorManager();
    this._config = config ?? createPipelineConfiguration();
  }

  public registerMiddleware(
    middleware: Partial<CommandMiddleware> & {
      name: string;
      execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
    },
  ): CommandMiddleware {
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
    return this._interceptorManager.registerInterceptor(interceptor);
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

    let beforeResult: MiddlewareResult = createMiddlewareResult();

    // 1. BEFORE Middleware Phase
    if (this._config.enableBeforeMiddleware) {
      beforeResult = await this._middlewareManager.executeBefore(context);
    }

    let executionResult: CommandExecutionResult<TResult>;
    let interceptorResult = undefined;

    try {
      // 2. Interceptor Chain & Executor Phase
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

      // Check if command execution failed
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

    // 3. AFTER Middleware Phase
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
