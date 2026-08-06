/**
 * Configuration Source Manager & Resolution Engine (Phase 16.3.2).
 *
 * Implements priority-based key resolution, entry extraction, merged dictionary generation,
 * and immutable configuration snapshot creation across registered configuration sources.
 */

import {
  ConfigurationEntry,
  ConfigurationSnapshot,
  createConfigurationEntry,
  createConfigurationSnapshot,
} from './models';
import { SourceRegistry } from './source_registry';

export class ConfigurationSourceManager {
  private readonly _registry: SourceRegistry;

  constructor(registry: SourceRegistry) {
    this._registry = registry;
  }

  public get<T = unknown>(key: string, defaultValue?: T): T | undefined {
    const k = key.trim();
    const sources = this._registry.listSources();

    for (const source of sources) {
      if (source.enabled && source.contains(k)) {
        return source.get(k) as T;
      }
    }

    return defaultValue;
  }

  public has(key: string): boolean {
    const k = key.trim();
    const sources = this._registry.listSources();

    for (const source of sources) {
      if (source.enabled && source.contains(k)) {
        return true;
      }
    }

    return false;
  }

  public getEntry(key: string): ConfigurationEntry | undefined {
    const k = key.trim();
    const sources = this._registry.listSources();

    for (const source of sources) {
      if (source.enabled && source.contains(k)) {
        const value = source.get(k);
        return createConfigurationEntry({
          key: k,
          value,
          sourceName: source.name,
          priority: source.priority,
        });
      }
    }

    return undefined;
  }

  public getAll(): Readonly<Record<string, unknown>> {
    const merged: Record<string, unknown> = {};
    const sources = Array.from(this._registry.listSources()).reverse();

    for (const source of sources) {
      if (source.enabled) {
        const items = source.items();
        for (const [k, v] of Object.entries(items)) {
          merged[k] = v;
        }
      }
    }

    return Object.freeze(merged);
  }

  public createSnapshot(): ConfigurationSnapshot {
    const mergedValues = this.getAll();
    const entries: Record<string, ConfigurationEntry> = {};

    for (const key of Object.keys(mergedValues)) {
      const entry = this.getEntry(key);
      if (entry) {
        entries[key] = entry;
      }
    }

    const activeSources = this._registry.listSources().filter((s) => s.enabled);

    return createConfigurationSnapshot({
      entries: Object.freeze(entries),
      mergedValues,
      sourceCount: activeSources.length,
      timestamp: new Date().toISOString(),
    });
  }
}
