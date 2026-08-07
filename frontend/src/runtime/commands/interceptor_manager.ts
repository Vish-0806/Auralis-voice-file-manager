/**
 * Interceptor Manager Implementation (Phase 16.6.4).
 *
 * Implements IInterceptorManager managing execution interceptor registration,
 * priority ordering, recursive interceptor chaining (around core execution),
 * execution wrapping, cancellation, context modification, and telemetry reporting.
 */

import {
  CommandExecutionContext,
  CommandExecutionResult,
  InterceptorExecution,
  InterceptorHandler,
  InterceptorRegistration,
  InterceptorResult,
  MiddlewarePriority,
  createInterceptorExecution,
  createInterceptorRegistration,
  createInterceptorResult,
} from './models';
import { CommandExecutionException } from './exceptions';
import { IInterceptorManager } from './interfaces';

export class InterceptorManager implements IInterceptorManager {
  private readonly _interceptors = new Map<string, InterceptorRegistration<any>>();

  public registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult> {
    if (!interceptor) {
      throw new CommandExecutionException('Interceptor registration cannot be null or undefined.');
    }
    if (!interceptor.name || !interceptor.name.trim()) {
      throw new CommandExecutionException('Interceptor name cannot be empty.');
    }
    if (!interceptor.intercept) {
      throw new CommandExecutionException('Interceptor intercept function cannot be null or undefined.');
    }

    const frozen = createInterceptorRegistration<TResult>({
      interceptorId: interceptor.interceptorId,
      name: interceptor.name.trim(),
      priority: interceptor.priority ?? MiddlewarePriority.NORMAL,
      enabled: interceptor.enabled ?? true,
      intercept: interceptor.intercept,
    });

    this._interceptors.set(frozen.interceptorId, frozen as any);
    return frozen;
  }

  public removeInterceptor(interceptorId: string): boolean {
    if (!interceptorId || !interceptorId.trim()) {
      return false;
    }
    return this._interceptors.delete(interceptorId.trim());
  }

  public listInterceptors(): ReadonlyArray<InterceptorRegistration> {
    const list = Array.from(this._interceptors.values());
    list.sort((a, b) => b.priority - a.priority);
    return Object.freeze(list);
  }

  public async executeChain<TResult = unknown>(
    context: CommandExecutionContext,
    coreExecution: () => Promise<CommandExecutionResult<TResult>>,
  ): Promise<InterceptorResult<TResult>> {
    const interceptors = Array.from(this._interceptors.values())
      .filter((i) => i.enabled)
      .sort((a, b) => b.priority - a.priority);

    const executions: InterceptorExecution[] = [];

    const dispatch = async (index: number): Promise<CommandExecutionResult<TResult>> => {
      if (index >= interceptors.length) {
        return coreExecution();
      }

      const interceptor = interceptors[index];
      const start = performance ? performance.now() : Date.now();

      try {
        const result = await interceptor.intercept(context, () => dispatch(index + 1));
        const end = performance ? performance.now() : Date.now();
        const durationMs = Math.max(0, Math.round((end - start) * 100) / 100);

        executions.push(
          createInterceptorExecution({
            interceptorId: interceptor.interceptorId,
            name: interceptor.name,
            success: true,
            durationMs,
          }),
        );

        return result;
      } catch (err: any) {
        const end = performance ? performance.now() : Date.now();
        const durationMs = Math.max(0, Math.round((end - start) * 100) / 100);

        executions.push(
          createInterceptorExecution({
            interceptorId: interceptor.interceptorId,
            name: interceptor.name,
            success: false,
            durationMs,
            error: err?.message ?? 'Interceptor execution failed.',
          }),
        );

        throw err;
      }
    };

    const finalResult = await dispatch(0);

    return createInterceptorResult<TResult>({
      executionResult: finalResult,
      executions,
      totalInterceptors: interceptors.length,
    });
  }

  public clear(): void {
    this._interceptors.clear();
  }
}
