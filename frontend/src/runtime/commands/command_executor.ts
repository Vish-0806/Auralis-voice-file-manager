/**
 * Command Executor Implementation (Phase 16.6.3).
 *
 * Implements ICommandExecutor managing handler registrations, synchronous &
 * asynchronous command execution pipelines, parameter validation, active execution
 * tracking, cancellation, bounded history retention, telemetry statistics, and health reporting.
 */

import {
  CommandDefinition,
  CommandExecutionConfiguration,
  CommandExecutionContext,
  CommandExecutionHealth,
  CommandExecutionRecord,
  CommandExecutionRequest,
  CommandExecutionResult,
  CommandExecutionStatistics,
  CommandExecutionStatus,
  CommandHandler,
  ExecutionDiagnostics,
  ExecutionError,
  ExecutionWarning,
  createCommandExecutionConfiguration,
  createCommandExecutionContext,
  createCommandExecutionHealth,
  createCommandExecutionRecord,
  createCommandExecutionResult,
  createCommandExecutionStatistics,
  createExecutionDiagnostics,
  createExecutionError,
  createExecutionTiming,
  createExecutionWarning,
} from './models';
import { CommandExecutionException } from './exceptions';
import { ICommandExecutor, ICommandRegistry } from './interfaces';
import { CommandRegistry } from './command_registry';

export class CommandExecutor implements ICommandExecutor {
  private readonly _registry: ICommandRegistry;
  private readonly _config: CommandExecutionConfiguration;

  private readonly _handlers = new Map<string, CommandHandler<any, any>>();
  private readonly _activeExecutions = new Map<string, CommandExecutionContext>();
  private readonly _history: CommandExecutionRecord[] = [];

  private _totalExecutions = 0;
  private _successfulExecutions = 0;
  private _failedExecutions = 0;
  private _cancelledExecutions = 0;
  private _validationFailures = 0;
  private _executionTimes: number[] = [];

  constructor(
    registry?: ICommandRegistry,
    config?: CommandExecutionConfiguration,
  ) {
    this._registry = registry ?? new CommandRegistry();
    this._config = config ?? createCommandExecutionConfiguration();
  }

  public registerHandler<TArgs = Record<string, unknown>, TResult = unknown>(
    commandId: string,
    handler: CommandHandler<TArgs, TResult>,
  ): void {
    if (!commandId || !commandId.trim()) {
      throw new CommandExecutionException('Command ID cannot be empty when registering a handler.');
    }
    if (!handler) {
      throw new CommandExecutionException('Command handler function cannot be null or undefined.');
    }

    const id = commandId.trim();
    this._handlers.set(id, handler);
  }

  public unregisterHandler(commandId: string): boolean {
    if (!commandId || !commandId.trim()) {
      return false;
    }
    return this._handlers.delete(commandId.trim());
  }

  public hasHandler(commandId: string): boolean {
    if (!commandId || !commandId.trim()) {
      return false;
    }
    return this._handlers.has(commandId.trim());
  }

  public execute<TResult = unknown>(
    request: CommandExecutionRequest,
  ): CommandExecutionResult<TResult> {
    this._totalExecutions++;
    const warnings: ExecutionWarning[] = [];
    const startTime = new Date();
    const startPerf = performance ? performance.now() : Date.now();

    const validation = this.pipelineValidate(request, warnings);
    if (!validation.valid || !validation.definition || !validation.handler) {
      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
      const timing = createExecutionTiming({
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs,
      });

      const context = createCommandExecutionContext({
        commandId: request?.commandId ?? 'unknown',
        mode: 'sync',
        args: request?.args ?? {},
        source: request?.source,
        userId: request?.userId,
        sessionId: request?.sessionId,
        correlationId: request?.correlationId,
        metadata: request?.metadata,
      });

      const result = createCommandExecutionResult<TResult>({
        commandId: request?.commandId ?? 'unknown',
        status: validation.status ?? CommandExecutionStatus.VALIDATION_FAILED,
        error: validation.error,
        warnings,
        timing,
        context,
      });

      this.recordHistory(result);
      return result;
    }

    const { definition, handler } = validation;

    const context = createCommandExecutionContext({
      commandId: definition.id,
      mode: 'sync',
      args: request.args ?? {},
      source: request.source,
      userId: request.userId,
      sessionId: request.sessionId,
      correlationId: request.correlationId,
      metadata: request.metadata,
    });

    this._activeExecutions.set(context.executionId, context);

    try {
      const valueOrPromise = handler(context.args, context);

      if (valueOrPromise && typeof (valueOrPromise as any).then === 'function') {
        // If an async handler was called synchronously, throw exception or handle error
        this._activeExecutions.delete(context.executionId);
        this._failedExecutions++;
        const endPerf = performance ? performance.now() : Date.now();
        const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
        const timing = createExecutionTiming({
          startTime: startTime.toISOString(),
          endTime: new Date().toISOString(),
          durationMs,
        });

        const error = createExecutionError({
          code: 'SYNC_EXECUTION_ASYNC_HANDLER',
          message: `Command handler for '${definition.id}' returned a Promise. Use executeAsync() for asynchronous handlers.`,
        });

        const result = createCommandExecutionResult<TResult>({
          commandId: definition.id,
          status: CommandExecutionStatus.FAILED,
          error,
          warnings,
          timing,
          context,
        });

        this.recordHistory(result);
        return result;
      }

      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
      this.recordTiming(durationMs);
      this._activeExecutions.delete(context.executionId);
      this._successfulExecutions++;

      const timing = createExecutionTiming({
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs,
      });

      const result = createCommandExecutionResult<TResult>({
        commandId: definition.id,
        status: CommandExecutionStatus.COMPLETED,
        value: valueOrPromise as TResult,
        warnings,
        timing,
        context,
      });

      this.recordHistory(result);
      return result;
    } catch (err: any) {
      this._activeExecutions.delete(context.executionId);
      this._failedExecutions++;
      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
      this.recordTiming(durationMs);

      const error = createExecutionError({
        code: err?.name ?? 'COMMAND_EXECUTION_FAILED',
        message: err?.message ?? 'Execution error occurred.',
        stack: err?.stack,
      });

      const timing = createExecutionTiming({
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs,
      });

      const result = createCommandExecutionResult<TResult>({
        commandId: definition.id,
        status: CommandExecutionStatus.FAILED,
        error,
        warnings,
        timing,
        context,
      });

      this.recordHistory(result);
      return result;
    }
  }

  public async executeAsync<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<CommandExecutionResult<TResult>> {
    this._totalExecutions++;
    const warnings: ExecutionWarning[] = [];
    const startTime = new Date();
    const startPerf = performance ? performance.now() : Date.now();

    const validation = this.pipelineValidate(request, warnings);
    if (!validation.valid || !validation.definition || !validation.handler) {
      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
      const timing = createExecutionTiming({
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs,
      });

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

      const result = createCommandExecutionResult<TResult>({
        commandId: request?.commandId ?? 'unknown',
        status: validation.status ?? CommandExecutionStatus.VALIDATION_FAILED,
        error: validation.error,
        warnings,
        timing,
        context,
      });

      this.recordHistory(result);
      return result;
    }

    const { definition, handler } = validation;

    const context = createCommandExecutionContext({
      commandId: definition.id,
      mode: 'async',
      args: request.args ?? {},
      source: request.source,
      userId: request.userId,
      sessionId: request.sessionId,
      correlationId: request.correlationId,
      metadata: request.metadata,
    });

    this._activeExecutions.set(context.executionId, context);

    try {
      const value = await Promise.resolve(handler(context.args, context));

      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
      this.recordTiming(durationMs);
      this._activeExecutions.delete(context.executionId);
      this._successfulExecutions++;

      const timing = createExecutionTiming({
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs,
      });

      const result = createCommandExecutionResult<TResult>({
        commandId: definition.id,
        status: CommandExecutionStatus.COMPLETED,
        value: value as TResult,
        warnings,
        timing,
        context,
      });

      this.recordHistory(result);
      return result;
    } catch (err: any) {
      this._activeExecutions.delete(context.executionId);
      this._failedExecutions++;
      const endPerf = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((endPerf - startPerf) * 100) / 100);
      this.recordTiming(durationMs);

      const error = createExecutionError({
        code: err?.name ?? 'COMMAND_EXECUTION_FAILED',
        message: err?.message ?? 'Async execution error occurred.',
        stack: err?.stack,
      });

      const timing = createExecutionTiming({
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs,
      });

      const result = createCommandExecutionResult<TResult>({
        commandId: definition.id,
        status: CommandExecutionStatus.FAILED,
        error,
        warnings,
        timing,
        context,
      });

      this.recordHistory(result);
      return result;
    }
  }

  public validateExecution(request: CommandExecutionRequest): CommandExecutionResult<boolean> {
    const warnings: ExecutionWarning[] = [];
    const validation = this.pipelineValidate(request, warnings);

    const context = createCommandExecutionContext({
      commandId: request?.commandId ?? 'unknown',
      mode: 'sync',
      args: request?.args ?? {},
      source: request?.source,
    });

    const timing = createExecutionTiming();

    return createCommandExecutionResult<boolean>({
      commandId: request?.commandId ?? 'unknown',
      status: validation.valid ? CommandExecutionStatus.COMPLETED : (validation.status ?? CommandExecutionStatus.VALIDATION_FAILED),
      value: validation.valid,
      error: validation.error,
      warnings,
      timing,
      context,
    });
  }

  public cancelExecution(executionId: string): boolean {
    if (!executionId || !executionId.trim()) {
      return false;
    }

    const id = executionId.trim();
    if (this._activeExecutions.has(id)) {
      this._activeExecutions.delete(id);
      this._cancelledExecutions++;
      return true;
    }

    return false;
  }

  public executionHistory(): ReadonlyArray<CommandExecutionRecord> {
    return Object.freeze([...this._history]);
  }

  public clearExecutionHistory(): void {
    this._history.length = 0;
  }

  public statistics(): CommandExecutionStatistics {
    const totalTimes = this._executionTimes.length;
    const avgTime = totalTimes > 0 ? this._executionTimes.reduce((a, b) => a + b, 0) / totalTimes : 0;
    const maxTime = totalTimes > 0 ? Math.max(...this._executionTimes) : 0;
    const minTime = totalTimes > 0 ? Math.min(...this._executionTimes) : 0;

    return createCommandExecutionStatistics({
      executions: this._totalExecutions,
      successfulExecutions: this._successfulExecutions,
      failedExecutions: this._failedExecutions,
      cancelledExecutions: this._cancelledExecutions,
      validationFailures: this._validationFailures,
      averageExecutionTime: Math.round(avgTime * 100) / 100,
      maximumExecutionTime: maxTime,
      minimumExecutionTime: minTime,
      historySize: this._history.length,
      activeExecutions: this._activeExecutions.size,
    });
  }

  public health(): CommandExecutionHealth {
    const stats = this.statistics();
    const totalEnded = stats.successfulExecutions + stats.failedExecutions;
    const failureRate = totalEnded > 0 ? Math.round((stats.failedExecutions / totalEnded) * 100) : 0;
    const successRate = totalEnded > 0 ? Math.round((stats.successfulExecutions / totalEnded) * 100) : 100;
    const healthy = failureRate <= 20 && stats.validationFailures < 50;

    return createCommandExecutionHealth({
      healthy,
      failureRate,
      successRate,
      averageExecutionTime: stats.averageExecutionTime,
      historyCapacity: this._config.maxHistorySize,
      activeExecutions: stats.activeExecutions,
      validationFailures: stats.validationFailures,
      executionThroughput: stats.executions,
      message: healthy
        ? 'Command execution engine is fully operational.'
        : `Command execution engine elevated failure rate (${failureRate}%).`,
    });
  }

  public diagnostics(): ExecutionDiagnostics {
    return createExecutionDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      historySize: this._history.length,
      activeExecutions: this._activeExecutions.size,
    });
  }

  private pipelineValidate(
    request: CommandExecutionRequest,
    warnings: ExecutionWarning[],
  ): {
    valid: boolean;
    definition?: CommandDefinition;
    handler?: CommandHandler<any, any>;
    status?: CommandExecutionStatus;
    error?: ExecutionError;
  } {
    if (!request) {
      this._validationFailures++;
      return {
        valid: false,
        status: CommandExecutionStatus.VALIDATION_FAILED,
        error: createExecutionError({
          code: 'INVALID_REQUEST',
          message: 'Execution request cannot be null or undefined.',
        }),
      };
    }

    if (!request.commandId || !request.commandId.trim()) {
      this._validationFailures++;
      return {
        valid: false,
        status: CommandExecutionStatus.VALIDATION_FAILED,
        error: createExecutionError({
          code: 'MISSING_COMMAND_ID',
          message: 'Command ID in execution request cannot be empty.',
        }),
      };
    }

    const commandId = request.commandId.trim();

    // 1. Lookup in registry (by ID or Alias)
    let definition = this._registry.findCommand(commandId);
    if (!definition) {
      definition = this._registry.findByAlias(commandId);
    }

    if (!definition) {
      this._validationFailures++;
      return {
        valid: false,
        status: CommandExecutionStatus.REJECTED,
        error: createExecutionError({
          code: 'UNKNOWN_COMMAND',
          message: `Command '${commandId}' is not registered.`,
        }),
      };
    }

    // 2. Check enabled
    if (!definition.enabled) {
      this._validationFailures++;
      return {
        valid: false,
        status: CommandExecutionStatus.REJECTED,
        error: createExecutionError({
          code: 'COMMAND_DISABLED',
          message: `Command '${definition.id}' is currently disabled.`,
        }),
      };
    }

    // 3. Check deprecated
    if (definition.deprecated) {
      warnings.push(
        createExecutionWarning({
          code: 'COMMAND_DEPRECATED',
          message: `Command '${definition.id}' is deprecated.`,
        }),
      );
    }

    // 4. Check handler
    const handler = this._handlers.get(definition.id);
    if (!handler) {
      this._validationFailures++;
      return {
        valid: false,
        status: CommandExecutionStatus.VALIDATION_FAILED,
        error: createExecutionError({
          code: 'MISSING_HANDLER',
          message: `No execution handler registered for command '${definition.id}'.`,
        }),
      };
    }

    // 5. Parameter validation
    if (definition.parameters && definition.parameters.length > 0) {
      const args = request.args ?? {};

      for (const param of definition.parameters) {
        const val = args[param.name];

        if (param.required && (val === undefined || val === null)) {
          this._validationFailures++;
          return {
            valid: false,
            status: CommandExecutionStatus.VALIDATION_FAILED,
            error: createExecutionError({
              code: 'MISSING_REQUIRED_PARAMETER',
              message: `Required parameter '${param.name}' is missing for command '${definition.id}'.`,
            }),
          };
        }

        if (val !== undefined && val !== null && param.type !== 'any') {
          let validParamType = true;
          switch (param.type) {
            case 'string':
              validParamType = typeof val === 'string';
              break;
            case 'number':
              validParamType = typeof val === 'number' && !isNaN(val);
              break;
            case 'boolean':
              validParamType = typeof val === 'boolean';
              break;
            case 'object':
              validParamType = typeof val === 'object' && !Array.isArray(val);
              break;
            case 'array':
              validParamType = Array.isArray(val);
              break;
          }

          if (!validParamType) {
            this._validationFailures++;
            return {
              valid: false,
              status: CommandExecutionStatus.VALIDATION_FAILED,
              error: createExecutionError({
                code: 'INVALID_PARAMETER_TYPE',
                message: `Parameter '${param.name}' must be of type '${param.type}', received '${typeof val}'.`,
              }),
            };
          }
        }
      }
    }

    return { valid: true, definition, handler };
  }

  private recordHistory(result: CommandExecutionResult<any>): void {
    const record = createCommandExecutionRecord({ result });
    this._history.push(record);

    while (this._history.length > this._config.maxHistorySize) {
      this._history.shift();
    }
  }

  private recordTiming(durationMs: number): void {
    this._executionTimes.push(durationMs);
    if (this._executionTimes.length > 1000) {
      this._executionTimes.shift();
    }
  }
}
