/**
 * Persistence Manager Engine (Phase 16.5).
 *
 * Implements IPersistenceManager providing an abstract state persistence layer,
 * version tracking, state restoration, snapshotting, and storage clearing.
 */

import { createPersistenceRecord, PersistenceRecord } from './models';
import { PersistenceException, StateValidationException } from './exceptions';
import { IPersistenceManager } from './interfaces';

export class PersistenceManager implements IPersistenceManager {
  private readonly _storage = new Map<string, { value: unknown; record: PersistenceRecord }>();

  public save<T = unknown>(containerId: string, key: string, state: T): PersistenceRecord {
    const cId = containerId ? containerId.trim() : '';
    const k = key ? key.trim() : '';

    if (!cId || !k) {
      throw new StateValidationException('Container ID and key are required for state persistence.');
    }
    if (state === undefined || state === null) {
      throw new PersistenceException('Cannot persist null or undefined state.');
    }

    const storageKey = `${cId}::${k}`;
    const existing = this._storage.get(storageKey);
    const version = existing ? existing.record.version + 1 : 1;

    const record = createPersistenceRecord({
      containerId: cId,
      key: k,
      version,
    });

    this._storage.set(storageKey, {
      value: this.deepClone(state),
      record,
    });

    return record;
  }

  public load<T = unknown>(containerId: string, key: string): T | undefined {
    const cId = containerId ? containerId.trim() : '';
    const k = key ? key.trim() : '';

    const storageKey = `${cId}::${k}`;
    const entry = this._storage.get(storageKey);
    if (!entry) return undefined;

    return this.deepClone(entry.value) as T;
  }

  public clear(containerId?: string): void {
    if (!containerId) {
      this._storage.clear();
      return;
    }

    const prefix = `${containerId.trim()}::`;
    for (const key of Array.from(this._storage.keys())) {
      if (key.startsWith(prefix)) {
        this._storage.delete(key);
      }
    }
  }

  public snapshot(): ReadonlyArray<PersistenceRecord> {
    const records = Array.from(this._storage.values()).map((e) => e.record);
    return Object.freeze(records);
  }

  private deepClone<V>(val: V): V {
    if (val === null || typeof val !== 'object') return val;
    try {
      return JSON.parse(JSON.stringify(val));
    } catch {
      return val;
    }
  }
}
