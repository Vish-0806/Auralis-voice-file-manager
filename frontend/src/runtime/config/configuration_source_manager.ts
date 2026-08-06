/**
 * Configuration Source Manager & Resolution Engine (Phase 16.3.5).
 *
 * Implements priority-based key resolution, entry extraction, merged dictionary generation,
 * active profile override integration, sensitive value protection, and immutable configuration snapshot creation across registered configuration sources.
 */

import {
  ConfigurationEntry,
  ConfigurationSnapshot,
  ConfigurationSourcePriority,
  createConfigurationEntry,
  createConfigurationSnapshot,
} from './models';
import { SourceRegistry } from './source_registry';
import { ProfileManager } from './profile_manager';
import { SecureConfigurationManager } from './secure_configuration_manager';

export class ConfigurationSourceManager {
  private readonly _registry: SourceRegistry;
  private readonly _profileManager?: ProfileManager;
  private readonly _secureManager?: SecureConfigurationManager;

  constructor(
    registry: SourceRegistry,
    profileManager?: ProfileManager,
    secureManager?: SecureConfigurationManager,
  ) {
    this._registry = registry;
    this._profileManager = profileManager;
    this._secureManager = secureManager;
  }

  public get<T = unknown>(key: string, defaultValue?: T): T | undefined {
    const k = key.trim();

    if (this._secureManager && this._secureManager.contains(k)) {
      return this._secureManager.getSensitiveValue(k) as T;
    }

    if (this._profileManager) {
      const overrides = this._profileManager.getMergedOverrides();
      if (k in overrides) {
        return overrides[k] as T;
      }
    }

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

    if (this._secureManager && this._secureManager.contains(k)) {
      return true;
    }

    if (this._profileManager) {
      const overrides = this._profileManager.getMergedOverrides();
      if (k in overrides) {
        return true;
      }
    }

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

    if (this._secureManager && this._secureManager.contains(k)) {
      const redacted = this._secureManager.getRedactedValue(k);
      return createConfigurationEntry({
        key: k,
        value: redacted,
        sourceName: 'SensitiveValue',
        priority: ConfigurationSourcePriority.SENSITIVE,
      });
    }

    if (this._profileManager) {
      const overrides = this._profileManager.getMergedOverrides();
      if (k in overrides) {
        const activeProf = this._profileManager.getActiveProfile();
        return createConfigurationEntry({
          key: k,
          value: overrides[k],
          sourceName: `Profile:${activeProf?.profileName ?? 'default'}`,
          priority: ConfigurationSourcePriority.PROFILE,
        });
      }
    }

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

    if (this._profileManager) {
      const overrides = this._profileManager.getMergedOverrides();
      for (const [k, v] of Object.entries(overrides)) {
        merged[k] = v;
      }
    }

    if (this._secureManager) {
      const snap = this._secureManager.createSnapshot();
      for (const ref of snap.references) {
        merged[ref.key] = ref.redactedValue;
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
