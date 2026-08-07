/**
 * Plugin Lifecycle Manager Engine (Phase 16.7).
 *
 * Implements IPluginLifecycleManager to orchestrate plugin lifecycles, enforce state machine
 * constraints, and log activation history.
 */

import {
  PluginLifecycleState,
  PluginState,
  PluginActivation,
  PluginDeactivation,
  PluginLifecycleRecord,
  createPluginState,
  createPluginActivation,
  createPluginDeactivation,
  createPluginLifecycleRecord,
} from './models';
import { IPluginLifecycleManager } from './interfaces';
import { PluginLifecycleException } from './exceptions';

export class PluginLifecycleManager implements IPluginLifecycleManager {
  private readonly _states = new Map<string, PluginState>();
  private readonly _history: PluginLifecycleRecord[] = [];

  public async initializePlugin(pluginId: string, context: unknown): Promise<PluginState> {
    const existing = this._states.get(pluginId);
    if (existing && existing.initialized) {
      return existing;
    }

    const state = createPluginState({
      pluginId,
      lifecycleState: PluginLifecycleState.INITIALIZED,
      initialized: true,
      activated: false,
      registeredAt: existing?.registeredAt ?? new Date().toISOString(),
    });

    this._states.set(pluginId, state);
    this.recordState(pluginId, state, 'Initialized plugin successfully.');
    return state;
  }

  public async activatePlugin(pluginId: string): Promise<PluginActivation> {
    const startTime = Date.now();
    const existing = this._states.get(pluginId);

    if (!existing || !existing.initialized) {
      throw new PluginLifecycleException(`Cannot activate uninitialized plugin '${pluginId}'.`);
    }

    if (existing.activated) {
      return createPluginActivation({
        pluginId,
        activatedAt: existing.activatedAt ?? new Date().toISOString(),
        durationMs: 0,
        success: true,
      });
    }

    const state = createPluginState({
      ...existing,
      lifecycleState: PluginLifecycleState.ACTIVATED,
      activated: true,
      activatedAt: new Date().toISOString(),
    });

    this._states.set(pluginId, state);
    this.recordState(pluginId, state, 'Activated plugin successfully.');

    return createPluginActivation({
      pluginId,
      activatedAt: state.activatedAt!,
      durationMs: Date.now() - startTime,
      success: true,
    });
  }

  public async deactivatePlugin(pluginId: string): Promise<PluginDeactivation> {
    const startTime = Date.now();
    const existing = this._states.get(pluginId);

    if (!existing || !existing.activated) {
      return createPluginDeactivation({
        pluginId,
        deactivatedAt: new Date().toISOString(),
        durationMs: 0,
        success: true,
      });
    }

    const state = createPluginState({
      ...existing,
      lifecycleState: PluginLifecycleState.DEACTIVATED,
      activated: false,
      activatedAt: undefined,
    });

    this._states.set(pluginId, state);
    this.recordState(pluginId, state, 'Deactivated plugin successfully.');

    return createPluginDeactivation({
      pluginId,
      deactivatedAt: new Date().toISOString(),
      durationMs: Date.now() - startTime,
      success: true,
    });
  }

  public async disposePlugin(pluginId: string): Promise<PluginState> {
    const existing = this._states.get(pluginId);
    if (!existing) {
      throw new PluginLifecycleException(`Plugin '${pluginId}' does not exist.`);
    }

    if (existing.activated) {
      await this.deactivatePlugin(pluginId);
    }

    const state = createPluginState({
      pluginId,
      lifecycleState: PluginLifecycleState.UNLOADED,
      initialized: false,
      activated: false,
    });

    this._states.set(pluginId, state);
    this.recordState(pluginId, state, 'Disposed/unloaded plugin.');
    return state;
  }

  public getHistory(pluginId?: string): ReadonlyArray<PluginLifecycleRecord> {
    if (pluginId) {
      return this._history.filter(h => h.pluginId === pluginId);
    }
    return this._history;
  }

  public recordState(pluginId: string, state: PluginState, desc?: string): void {
    this._history.push(
      createPluginLifecycleRecord({
        pluginId,
        state: state.lifecycleState,
        timestamp: new Date().toISOString(),
        description: desc,
      }),
    );
  }
}
