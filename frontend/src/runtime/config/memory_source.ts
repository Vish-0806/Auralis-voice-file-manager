/**
 * Memory Configuration Source Implementation (Phase 16.3.2).
 *
 * Implements an in-memory configuration source backed by Map<string, unknown>
 * with default priority ConfigurationSourcePriority.MEMORY (500).
 */

import { ConfigurationSourcePriority } from './models';
import { ConfigurationSource } from './configuration_source';

export class MemoryConfigurationSource extends ConfigurationSource {
  public readonly name: string;
  public readonly priority: number;

  private readonly _store = new Map<string, unknown>();

  constructor(
    name = 'MemorySource',
    priority: number = ConfigurationSourcePriority.MEMORY,
    initialValues?: Record<string, unknown>,
  ) {
    super();
    this.name = name;
    this.priority = priority;

    if (initialValues) {
      for (const [k, v] of Object.entries(initialValues)) {
        this._store.set(k, v);
      }
    }
  }

  public contains(key: string): boolean {
    const k = key.trim();
    const found = this._store.has(k);
    this._recordRead(found);
    return found;
  }

  public get(key: string): unknown | undefined {
    const k = key.trim();
    const found = this._store.has(k);
    this._recordRead(found);
    return this._store.get(k);
  }

  public set(key: string, value: unknown): boolean {
    const k = key.trim();
    this._store.set(k, value);
    this._recordWrite();
    return true;
  }

  public remove(key: string): boolean {
    const k = key.trim();
    const existed = this._store.delete(k);
    if (existed) {
      this._recordDelete();
    }
    return existed;
  }

  public clear(): void {
    this._store.clear();
    this._recordDelete();
  }

  public keys(): ReadonlyArray<string> {
    return Object.freeze(Array.from(this._store.keys()));
  }

  public values(): ReadonlyArray<unknown> {
    return Object.freeze(Array.from(this._store.values()));
  }

  public items(): Readonly<Record<string, unknown>> {
    const dict: Record<string, unknown> = {};
    for (const [k, v] of Array.from(this._store.entries())) {
      dict[k] = v;
    }
    return Object.freeze(dict);
  }
}
