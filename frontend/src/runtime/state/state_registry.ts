/**
 * State Registry Engine (Phase 16.5).
 *
 * Implements IStateRegistry managing registered stores, containers, lookup discovery,
 * duplicate detection, and registry telemetry reporting.
 */

import { StateContainer } from './models';
import { StateProviderException, StateValidationException } from './exceptions';
import { IStateRegistry, IStore } from './interfaces';

export class StateRegistry implements IStateRegistry {
  private readonly _stores = new Map<string, IStore>();
  private readonly _containers = new Map<string, StateContainer>();

  private _registrationCount = 0;
  private _unregistrationCount = 0;
  private _duplicatesRejected = 0;

  public registerStore(storeId: string, store: IStore): void {
    const id = storeId ? storeId.trim() : '';
    if (!id) {
      throw new StateValidationException('Store ID cannot be empty.');
    }
    if (!store) {
      throw new StateValidationException('Store cannot be null or undefined.');
    }
    if (this._stores.has(id)) {
      this._duplicatesRejected++;
      throw new StateProviderException(`Store ID '${id}' is already registered.`);
    }

    this._stores.set(id, store);
    this._registrationCount++;
  }

  public unregisterStore(storeId: string): boolean {
    const id = storeId ? storeId.trim() : '';
    const res = this._stores.delete(id);
    if (res) this._unregistrationCount++;
    return res;
  }

  public getStore(storeId: string): IStore | undefined {
    return this._stores.get(storeId.trim());
  }

  public listStores(): ReadonlyArray<string> {
    return Object.freeze(Array.from(this._stores.keys()));
  }

  public registerContainer<T = unknown>(container: StateContainer<T>): void {
    if (!container) {
      throw new StateValidationException('State container cannot be null or undefined.');
    }
    const name = container.name ? container.name.trim() : '';
    if (!name) {
      throw new StateValidationException('State container name cannot be empty.');
    }
    if (this._containers.has(name)) {
      this._duplicatesRejected++;
      throw new StateProviderException(`State container '${name}' is already registered.`);
    }

    this._containers.set(name, container as any);
    this._registrationCount++;
  }

  public unregisterContainer(name: string): boolean {
    const key = name ? name.trim() : '';
    const res = this._containers.delete(key);
    if (res) this._unregistrationCount++;
    return res;
  }

  public getContainer<T = unknown>(name: string): StateContainer<T> | undefined {
    return this._containers.get(name.trim()) as StateContainer<T> | undefined;
  }

  public listContainers(): ReadonlyArray<StateContainer> {
    return Object.freeze(Array.from(this._containers.values()));
  }

  public clear(): void {
    this._stores.clear();
    this._containers.clear();
  }

  public telemetry(): {
    registrationCount: number;
    unregistrationCount: number;
    duplicatesRejected: number;
  } {
    return Object.freeze({
      registrationCount: this._registrationCount,
      unregistrationCount: this._unregistrationCount,
      duplicatesRejected: this._duplicatesRejected,
    });
  }
}
