/**
 * State Container Engine (Phase 16.5).
 *
 * Implements IStateContainer providing deep immutability, state mutation operations
 * (set, replace, merge, reset, clone, freeze), version tracking, and container management.
 */

import { createStateContainer, StateContainer } from './models';
import { StateValidationException } from './exceptions';
import { IStateContainer } from './interfaces';

export class StateContainerEngine<T = unknown> implements IStateContainer<T> {
  private _currentContainer: StateContainer<T>;
  private readonly _initialState: T;

  constructor(name: string, initialState: T) {
    if (!name || !name.trim()) {
      throw new StateValidationException('State container name cannot be empty.');
    }
    if (initialState === undefined || initialState === null) {
      throw new StateValidationException('Initial state cannot be null or undefined.');
    }

    this._initialState = this.deepClone(initialState);
    this._currentContainer = createStateContainer<T>({
      name: name.trim(),
      state: this.deepClone(initialState),
      version: 1,
    });
  }

  public getState(): T {
    return this.deepClone(this._currentContainer.state);
  }

  public setState(newState: T): StateContainer<T> {
    if (newState === undefined || newState === null) {
      throw new StateValidationException('State payload cannot be null or undefined.');
    }

    const cloned = this.deepClone(newState);
    this._currentContainer = createStateContainer<T>({
      containerId: this._currentContainer.containerId,
      name: this._currentContainer.name,
      state: cloned,
      version: this._currentContainer.version + 1,
    });

    return this._currentContainer;
  }

  public replaceState(newState: T): StateContainer<T> {
    return this.setState(newState);
  }

  public mergeState(partialState: Partial<T>): StateContainer<T> {
    if (typeof this._currentContainer.state !== 'object' || this._currentContainer.state === null) {
      throw new StateValidationException('Cannot merge partial state into non-object state.');
    }

    const merged = { ...this._currentContainer.state, ...partialState } as T;
    return this.setState(merged);
  }

  public resetState(): StateContainer<T> {
    return this.setState(this._initialState);
  }

  public cloneState(): T {
    return this.deepClone(this._currentContainer.state);
  }

  public freezeState(): T {
    return Object.freeze(this.deepClone(this._currentContainer.state));
  }

  public getContainer(): StateContainer<T> {
    return this._currentContainer;
  }

  private deepClone<V>(val: V): V {
    if (val === null || typeof val !== 'object') {
      return val;
    }
    try {
      return JSON.parse(JSON.stringify(val));
    } catch {
      return val;
    }
  }
}
