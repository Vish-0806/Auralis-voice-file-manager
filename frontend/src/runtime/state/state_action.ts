/**
 * Action Dispatcher Engine (Phase 16.5).
 *
 * Implements IActionDispatcher handling action registration, synchronous and asynchronous dispatch pipelines,
 * action validation, action history logging, and dispatch telemetry.
 */

import { Action, createAction } from './models';
import { StateDispatchException, StateValidationException } from './exceptions';
import { IActionDispatcher } from './interfaces';

export class ActionDispatcher implements IActionDispatcher {
  private readonly _registeredActions = new Set<string>();
  private readonly _history: Action[] = [];
  private readonly _maxHistorySize: number;

  constructor(maxHistorySize = 100) {
    this._maxHistorySize = maxHistorySize;
  }

  public registerAction(type: string): void {
    const key = type ? type.trim() : '';
    if (!key) {
      throw new StateValidationException('Action type cannot be empty.');
    }
    this._registeredActions.add(key);
  }

  public dispatch<T = unknown>(action: Action<T>): Action<T> {
    if (!action) {
      throw new StateDispatchException('Cannot dispatch null or undefined action.');
    }
    const type = action.type ? action.type.trim() : '';
    if (!type) {
      throw new StateValidationException('Action type cannot be empty.');
    }

    const frozenAction = createAction<T>({
      type,
      payload: action.payload,
      actionId: action.actionId,
      metadata: action.metadata,
    });

    this._history.push(frozenAction as any);
    if (this._history.length > this._maxHistorySize) {
      this._history.shift();
    }

    return frozenAction;
  }

  public async dispatchAsync<T = unknown>(action: Action<T>): Promise<Action<T>> {
    return Promise.resolve(this.dispatch(action));
  }

  public listActions(): ReadonlyArray<string> {
    return Object.freeze(Array.from(this._registeredActions));
  }

  public history(): ReadonlyArray<Action> {
    return Object.freeze([...this._history]);
  }

  public clearHistory(): void {
    this._history.length = 0;
  }
}
