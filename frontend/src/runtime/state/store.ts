/**
 * State Store Implementation (Phase 16.5).
 *
 * Implements IStore managing multiple named StateContainer instances,
 * store snapshots, operations statistics, and health metrics.
 */

import {
  createStoreHealth,
  createStoreSnapshot,
  createStoreStatistics,
  StateContainer,
  StoreHealth,
  StoreSnapshot,
  StoreStatistics,
} from './models';
import { StateProviderException, StateValidationException } from './exceptions';
import { IStateContainer, IStore } from './interfaces';
import { StateContainerEngine } from './state_container';

export class StateStore implements IStore {
  private readonly _storeId: string;
  private readonly _containers = new Map<string, StateContainerEngine>();

  private _readCount = 0;
  private _writeCount = 0;
  private _updateCount = 0;
  private _resetCount = 0;

  constructor(storeId = 'default_store') {
    this._storeId = storeId;
  }

  public createContainer<T = unknown>(name: string, initialState: T): StateContainer<T> {
    const key = name ? name.trim() : '';
    if (!key) {
      throw new StateValidationException('Container name cannot be empty.');
    }
    if (this._containers.has(key)) {
      throw new StateProviderException(`State container '${key}' already exists in store.`);
    }

    const engine = new StateContainerEngine<T>(key, initialState);
    this._containers.set(key, engine as any);
    this._writeCount++;

    return engine.getContainer();
  }

  public getContainerEngine<T = unknown>(name: string): IStateContainer<T> | undefined {
    const key = name ? name.trim() : '';
    this._readCount++;
    return this._containers.get(key) as IStateContainer<T> | undefined;
  }

  public getContainer<T = unknown>(name: string): StateContainer<T> | undefined {
    const engine = this.getContainerEngine<T>(name);
    return engine ? engine.getContainer() : undefined;
  }

  public removeContainer(name: string): boolean {
    const key = name ? name.trim() : '';
    return this._containers.delete(key);
  }

  public listContainers(): ReadonlyArray<StateContainer> {
    this._readCount++;
    return Object.freeze(Array.from(this._containers.values()).map((c) => c.getContainer()));
  }

  public snapshotStore(): StoreSnapshot {
    const snapshotMap: Record<string, unknown> = {};
    for (const [key, engine] of this._containers.entries()) {
      snapshotMap[key] = engine.getState();
    }

    return createStoreSnapshot({
      storeId: this._storeId,
      state: Object.freeze(snapshotMap),
    });
  }

  public statistics(): StoreStatistics {
    return createStoreStatistics({
      readCount: this._readCount,
      writeCount: this._writeCount,
      updateCount: this._updateCount,
      resetCount: this._resetCount,
    });
  }

  public health(): StoreHealth {
    return createStoreHealth({
      healthy: true,
      activeContainers: this._containers.size,
      errorRate: 0,
    });
  }
}
