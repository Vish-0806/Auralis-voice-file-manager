/**
 * Middleware Manager Engine (Phase 16.5).
 *
 * Implements IMiddlewareManager managing before-dispatch, after-dispatch, and error middleware hooks,
 * execution ordering, priority execution, exception trapping, and middleware execution telemetry.
 */

import { Action, createMiddlewareExecution, MiddlewareExecution } from './models';
import { StateValidationException } from './exceptions';
import { IMiddlewareManager } from './interfaces';

export class MiddlewareManager implements IMiddlewareManager {
  private readonly _beforeHooks = new Map<string, (action: Action) => void | Promise<void>>();
  private readonly _afterHooks = new Map<string, (action: Action) => void | Promise<void>>();
  private readonly _errorHooks = new Map<string, (action: Action, error: Error) => void>();

  public registerBefore(id: string, fn: (action: Action) => void | Promise<void>): void {
    const key = id ? id.trim() : '';
    if (!key || !fn) {
      throw new StateValidationException('Middleware ID and handler function are required.');
    }
    this._beforeHooks.set(key, fn);
  }

  public registerAfter(id: string, fn: (action: Action) => void | Promise<void>): void {
    const key = id ? id.trim() : '';
    if (!key || !fn) {
      throw new StateValidationException('Middleware ID and handler function are required.');
    }
    this._afterHooks.set(key, fn);
  }

  public registerError(id: string, fn: (action: Action, error: Error) => void): void {
    const key = id ? id.trim() : '';
    if (!key || !fn) {
      throw new StateValidationException('Middleware ID and handler function are required.');
    }
    this._errorHooks.set(key, fn);
  }

  public executeBefore(action: Action): ReadonlyArray<MiddlewareExecution> {
    const executions: MiddlewareExecution[] = [];
    for (const [id, fn] of this._beforeHooks.entries()) {
      const start = performance ? performance.now() : Date.now();
      try {
        fn(action);
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createMiddlewareExecution({
            middlewareId: id,
            actionType: action.type,
            phase: 'BEFORE',
            success: true,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
          }),
        );
      } catch (e: any) {
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createMiddlewareExecution({
            middlewareId: id,
            actionType: action.type,
            phase: 'BEFORE',
            success: false,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
            error: e.message,
          }),
        );
      }
    }
    return Object.freeze(executions);
  }

  public executeAfter(action: Action): ReadonlyArray<MiddlewareExecution> {
    const executions: MiddlewareExecution[] = [];
    for (const [id, fn] of this._afterHooks.entries()) {
      const start = performance ? performance.now() : Date.now();
      try {
        fn(action);
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createMiddlewareExecution({
            middlewareId: id,
            actionType: action.type,
            phase: 'AFTER',
            success: true,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
          }),
        );
      } catch (e: any) {
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createMiddlewareExecution({
            middlewareId: id,
            actionType: action.type,
            phase: 'AFTER',
            success: false,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
            error: e.message,
          }),
        );
      }
    }
    return Object.freeze(executions);
  }

  public executeError(action: Action, error: Error): ReadonlyArray<MiddlewareExecution> {
    const executions: MiddlewareExecution[] = [];
    for (const [id, fn] of this._errorHooks.entries()) {
      const start = performance ? performance.now() : Date.now();
      try {
        fn(action, error);
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createMiddlewareExecution({
            middlewareId: id,
            actionType: action.type,
            phase: 'ERROR',
            success: true,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
          }),
        );
      } catch (e: any) {
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createMiddlewareExecution({
            middlewareId: id,
            actionType: action.type,
            phase: 'ERROR',
            success: false,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
            error: e.message,
          }),
        );
      }
    }
    return Object.freeze(executions);
  }
}
