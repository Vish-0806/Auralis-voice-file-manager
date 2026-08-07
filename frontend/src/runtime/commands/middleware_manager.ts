/**
 * Middleware Manager Implementation (Phase 16.6.4).
 *
 * Implements IMiddlewareManager managing before, after, and exception middleware
 * registration, priority ordering, phase-based execution, error isolation,
 * statistics telemetry, and health reporting.
 */

import {
  CommandExecutionContext,
  CommandExecutionResult,
  CommandMiddleware,
  MiddlewareExecution,
  MiddlewareHealth,
  MiddlewarePriority,
  MiddlewareResult,
  MiddlewareStatistics,
  createCommandMiddleware,
  createMiddlewareExecution,
  createMiddlewareHealth,
  createMiddlewareResult,
  createMiddlewareStatistics,
} from './models';
import { CommandExecutionException } from './exceptions';
import { IMiddlewareManager } from './interfaces';

export class MiddlewareManager implements IMiddlewareManager {
  private readonly _middlewares = new Map<string, CommandMiddleware>();

  private _totalExecutions = 0;
  private _failedExecutions = 0;
  private _executionTimes: number[] = [];

  public registerMiddleware(
    middleware: Partial<CommandMiddleware> & {
      name: string;
      execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
    },
  ): CommandMiddleware {
    if (!middleware) {
      throw new CommandExecutionException('Middleware registration cannot be null or undefined.');
    }
    if (!middleware.name || !middleware.name.trim()) {
      throw new CommandExecutionException('Middleware name cannot be empty.');
    }
    if (!middleware.execute) {
      throw new CommandExecutionException('Middleware execute function cannot be null or undefined.');
    }

    const frozen = createCommandMiddleware({
      middlewareId: middleware.middlewareId,
      name: middleware.name.trim(),
      phase: middleware.phase ?? 'BEFORE',
      priority: middleware.priority ?? MiddlewarePriority.NORMAL,
      enabled: middleware.enabled ?? true,
      execute: middleware.execute,
    });

    this._middlewares.set(frozen.middlewareId, frozen);
    return frozen;
  }

  public removeMiddleware(middlewareId: string): boolean {
    if (!middlewareId || !middlewareId.trim()) {
      return false;
    }
    return this._middlewares.delete(middlewareId.trim());
  }

  public listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware> {
    const all = Array.from(this._middlewares.values());
    const filtered = phase ? all.filter((m) => m.phase === phase) : all;
    filtered.sort((a, b) => b.priority - a.priority);
    return Object.freeze(filtered);
  }

  public async executeBefore(context: CommandExecutionContext): Promise<MiddlewareResult> {
    return this.runPhase('BEFORE', context);
  }

  public async executeAfter(
    context: CommandExecutionContext,
    result: CommandExecutionResult,
  ): Promise<MiddlewareResult> {
    return this.runPhase('AFTER', context, result);
  }

  public async executeException(
    context: CommandExecutionContext,
    error: Error,
  ): Promise<MiddlewareResult> {
    return this.runPhase('EXCEPTION', context, undefined, error);
  }

  public statistics(): MiddlewareStatistics {
    const all = Array.from(this._middlewares.values());
    const beforeCount = all.filter((m) => m.phase === 'BEFORE').length;
    const afterCount = all.filter((m) => m.phase === 'AFTER').length;
    const exceptionCount = all.filter((m) => m.phase === 'EXCEPTION').length;

    const avgMs =
      this._executionTimes.length > 0
        ? this._executionTimes.reduce((a, b) => a + b, 0) / this._executionTimes.length
        : 0;

    return createMiddlewareStatistics({
      totalRegistered: all.length,
      beforeCount,
      afterCount,
      exceptionCount,
      totalExecutions: this._totalExecutions,
      failedExecutions: this._failedExecutions,
      averageExecutionMs: Math.round(avgMs * 100) / 100,
    });
  }

  public health(): MiddlewareHealth {
    const activeMiddlewares = Array.from(this._middlewares.values()).filter((m) => m.enabled).length;
    const failureRate =
      this._totalExecutions > 0
        ? Math.round((this._failedExecutions / this._totalExecutions) * 100)
        : 0;
    const healthy = failureRate <= 10;

    return createMiddlewareHealth({
      healthy,
      activeMiddlewares,
      failureRate,
      message: healthy
        ? 'Middleware manager operational.'
        : `Middleware manager elevated failure rate (${failureRate}%).`,
    });
  }

  public clear(): void {
    this._middlewares.clear();
    this._totalExecutions = 0;
    this._failedExecutions = 0;
    this._executionTimes.length = 0;
  }

  private async runPhase(
    phase: 'BEFORE' | 'AFTER' | 'EXCEPTION',
    context: CommandExecutionContext,
    result?: CommandExecutionResult,
    error?: Error,
  ): Promise<MiddlewareResult> {
    const middlewares = Array.from(this._middlewares.values())
      .filter((m) => m.enabled && m.phase === phase)
      .sort((a, b) => b.priority - a.priority);

    const executions: MiddlewareExecution[] = [];

    for (const mw of middlewares) {
      this._totalExecutions++;
      const start = performance ? performance.now() : Date.now();

      try {
        await mw.execute(context, result, error);
        const end = performance ? performance.now() : Date.now();
        const durationMs = Math.max(0, Math.round((end - start) * 100) / 100);
        this.recordTiming(durationMs);

        executions.push(
          createMiddlewareExecution({
            middlewareId: mw.middlewareId,
            name: mw.name,
            phase: mw.phase,
            success: true,
            durationMs,
          }),
        );
      } catch (err: any) {
        this._failedExecutions++;
        const end = performance ? performance.now() : Date.now();
        const durationMs = Math.max(0, Math.round((end - start) * 100) / 100);
        this.recordTiming(durationMs);

        executions.push(
          createMiddlewareExecution({
            middlewareId: mw.middlewareId,
            name: mw.name,
            phase: mw.phase,
            success: false,
            durationMs,
            error: err?.message ?? 'Middleware execution failed.',
          }),
        );
      }
    }

    return createMiddlewareResult({ executions });
  }

  private recordTiming(durationMs: number): void {
    this._executionTimes.push(durationMs);
    if (this._executionTimes.length > 1000) {
      this._executionTimes.shift();
    }
  }
}
