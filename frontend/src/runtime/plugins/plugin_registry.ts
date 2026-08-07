/**
 * Plugin Registry Implementation (Phase 16.7).
 *
 * Implements IPluginRegistry to manage plugin manifests, metadata,
 * aliases, tags, categories, duplicates detection, registry health, and statistics.
 */

import {
  PluginDescriptor,
  PluginManifest,
  PluginRegistration,
  PluginState,
  PluginHealth,
  PluginLifecycleState,
  createPluginDescriptor,
  createPluginRegistration,
  createPluginState,
  createPluginHealth,
} from './models';
import { IPluginRegistry } from './interfaces';
import { PluginRegistrationException } from './exceptions';

export class PluginRegistry implements IPluginRegistry {
  private readonly _plugins = new Map<string, PluginDescriptor>();
  private readonly _states = new Map<string, PluginState>();
  private _lookupsCount = 0;
  private _searchCount = 0;
  private _registrationAttempts = 0;
  private _failedRegistrations = 0;

  public registerPlugin(manifest: PluginManifest, details: Partial<PluginDescriptor> = {}): PluginRegistration {
    this._registrationAttempts++;
    if (!manifest.id) {
      this._failedRegistrations++;
      throw new PluginRegistrationException('Plugin ID is missing from manifest.');
    }
    if (this._plugins.has(manifest.id)) {
      this._failedRegistrations++;
      throw new PluginRegistrationException(`Plugin with ID '${manifest.id}' is already registered.`);
    }

    const descriptor = createPluginDescriptor({
      id: manifest.id,
      manifest,
      loadPath: details.loadPath,
      checksum: details.checksum,
    });

    this._plugins.set(manifest.id, descriptor);

    const state = createPluginState({
      pluginId: manifest.id,
      lifecycleState: PluginLifecycleState.REGISTERED,
      initialized: false,
      activated: false,
      registeredAt: new Date().toISOString(),
    });
    this._states.set(manifest.id, state);

    return createPluginRegistration({
      pluginId: manifest.id,
      registeredAt: state.registeredAt,
      success: true,
    });
  }

  public removePlugin(pluginId: string): { pluginId: string; success: boolean; durationMs: number } {
    if (!this._plugins.has(pluginId)) {
      return { pluginId, success: false, durationMs: 0 };
    }
    this._plugins.delete(pluginId);
    this._states.delete(pluginId);
    return { pluginId, success: true, durationMs: 0 };
  }

  public updatePluginState(pluginId: string, updates: Partial<PluginState>): PluginState {
    const existing = this._states.get(pluginId);
    if (!existing) {
      throw new PluginRegistrationException(`Cannot update state for unregistered plugin '${pluginId}'.`);
    }
    const updated = createPluginState({
      ...existing,
      ...updates,
      pluginId,
    });
    this._states.set(pluginId, updated);
    return updated;
  }

  public findPlugin(pluginId: string): PluginDescriptor | undefined {
    this._lookupsCount++;
    return this._plugins.get(pluginId);
  }

  public containsPlugin(pluginId: string): boolean {
    return this._plugins.has(pluginId);
  }

  public listPlugins(): ReadonlyArray<PluginDescriptor> {
    return Array.from(this._plugins.values());
  }

  public listStates(): ReadonlyArray<PluginState> {
    return Array.from(this._states.values());
  }

  public findPluginsByCategory(category: string): ReadonlyArray<PluginDescriptor> {
    this._searchCount++;
    return Array.from(this._plugins.values()).filter(p => {
      // Find within capabilities or metadata
      return p.manifest.capabilities.some(c => c.type === 'category' && c.name === category);
    });
  }

  public findPluginsByTag(tag: string): ReadonlyArray<PluginDescriptor> {
    this._searchCount++;
    return Array.from(this._plugins.values()).filter(p => {
      return p.manifest.metadata.keywords?.includes(tag) || false;
    });
  }

  public search(query: string): ReadonlyArray<PluginDescriptor> {
    this._searchCount++;
    const lowerQuery = query.toLowerCase();
    return Array.from(this._plugins.values()).filter(p => {
      return (
        p.id.toLowerCase().includes(lowerQuery) ||
        p.manifest.name.toLowerCase().includes(lowerQuery) ||
        p.manifest.description.toLowerCase().includes(lowerQuery)
      );
    });
  }

  public statistics(): Record<string, number> {
    return {
      registeredPlugins: this._plugins.size,
      registrationAttempts: this._registrationAttempts,
      failedRegistrations: this._failedRegistrations,
      lookupsCount: this._lookupsCount,
      searchCount: this._searchCount,
    };
  }

  public health(): PluginHealth {
    const issues: string[] = [];
    const plugins = Array.from(this._plugins.values());
    const states = Array.from(this._states.values());

    for (const state of states) {
      if (state.lifecycleState === PluginLifecycleState.FAILED) {
        issues.push(`Plugin '${state.pluginId}' is in a failed state: ${state.error ?? 'unknown error'}`);
      }
    }

    return createPluginHealth({
      pluginId: 'registry',
      healthy: issues.length === 0,
      lifecycleState: PluginLifecycleState.INITIALIZED,
      issues,
      message: issues.length === 0 ? 'Plugin Registry is healthy.' : 'Registry contains failed plugins.',
    });
  }

  public clear(): void {
    this._plugins.clear();
    this._states.clear();
    this._lookupsCount = 0;
    this._searchCount = 0;
    this._registrationAttempts = 0;
    this._failedRegistrations = 0;
  }
}
