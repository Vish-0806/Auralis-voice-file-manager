/**
 * Abstract Configuration Source Base Class (Phase 16.3.2).
 *
 * Provides shared state, telemetry metrics tracking, and health evaluation snapshots
 * for all IConfigurationSource implementations.
 */

import {
  ConfigurationSourceHealth,
  ConfigurationSourceStatistics,
  createConfigurationSourceHealth,
  createConfigurationSourceStatistics,
} from './models';
import { IConfigurationSource } from './interfaces';

export abstract class ConfigurationSource implements IConfigurationSource {
  public abstract readonly name: string;
  public abstract readonly priority: number;

  protected _enabled = true;
  protected _reads = 0;
  protected _writes = 0;
  protected _deletes = 0;
  protected _hits = 0;
  protected _misses = 0;

  public get enabled(): boolean {
    return this._enabled;
  }

  public abstract contains(key: string): boolean;
  public abstract get(key: string): unknown | undefined;
  public abstract set(key: string, value: unknown): boolean;
  public abstract remove(key: string): boolean;
  public abstract clear(): void;
  public abstract keys(): ReadonlyArray<string>;
  public abstract values(): ReadonlyArray<unknown>;
  public abstract items(): Readonly<Record<string, unknown>>;

  public health(): ConfigurationSourceHealth {
    return createConfigurationSourceHealth({
      healthy: this._enabled,
      sourceName: this.name,
      enabled: this._enabled,
      message: this._enabled
        ? `Source '${this.name}' is active and operational.`
        : `Source '${this.name}' is disabled.`,
    });
  }

  public statistics(): ConfigurationSourceStatistics {
    return createConfigurationSourceStatistics({
      reads: this._reads,
      writes: this._writes,
      deletes: this._deletes,
      hits: this._hits,
      misses: this._misses,
      itemCount: this.keys().length,
    });
  }

  protected _recordRead(hit: boolean): void {
    this._reads++;
    if (hit) {
      this._hits++;
    } else {
      this._misses++;
    }
  }

  protected _recordWrite(): void {
    this._writes++;
  }

  protected _recordDelete(): void {
    this._deletes++;
  }
}
