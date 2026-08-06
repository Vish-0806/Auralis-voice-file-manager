/**
 * Reducer Engine (Phase 16.5).
 *
 * Implements IReducerEngine managing pure reducer registration, ordered execution,
 * exception isolation, execution duration metrics, and reducer state mutation reporting.
 */

import { Action, createReducerExecution, Reducer, ReducerExecution } from './models';
import { ReducerException, StateValidationException } from './exceptions';
import { IReducerEngine } from './interfaces';

export class ReducerEngine implements IReducerEngine {
  private readonly _reducers = new Map<string, Reducer>();

  public registerReducer<S = unknown, A = Action>(reducer: Reducer<S, A>): void {
    if (!reducer) {
      throw new StateValidationException('Reducer cannot be null or undefined.');
    }
    if (!reducer.name || !reducer.name.trim()) {
      throw new StateValidationException('Reducer name cannot be empty.');
    }
    if (!reducer.reduce) {
      throw new StateValidationException('Reducer reduce function cannot be undefined.');
    }
    if (this._reducers.has(reducer.reducerId)) {
      throw new ReducerException(`Reducer ID '${reducer.reducerId}' is already registered.`);
    }

    this._reducers.set(reducer.reducerId, reducer as any);
  }

  public removeReducer(reducerId: string): boolean {
    return this._reducers.delete(reducerId.trim());
  }

  public executeReducers<S = unknown, A = Action>(
    state: S,
    action: A,
  ): { newState: S; executions: ReadonlyArray<ReducerExecution> } {
    let currentState = state;
    const executions: ReducerExecution[] = [];
    const actionType = (action as any)?.type ?? 'UNKNOWN';

    for (const reducer of this._reducers.values()) {
      const start = performance ? performance.now() : Date.now();
      try {
        currentState = (reducer as Reducer<S, A>).reduce(currentState, action);
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createReducerExecution({
            reducerId: reducer.reducerId,
            actionType,
            success: true,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
          }),
        );
      } catch (e: any) {
        const end = performance ? performance.now() : Date.now();
        executions.push(
          createReducerExecution({
            reducerId: reducer.reducerId,
            actionType,
            success: false,
            durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
            error: e.message ?? 'Reducer execution error',
          }),
        );
      }
    }

    return {
      newState: currentState,
      executions: Object.freeze(executions),
    };
  }

  public listReducers(): ReadonlyArray<Reducer> {
    return Object.freeze(Array.from(this._reducers.values()));
  }
}
