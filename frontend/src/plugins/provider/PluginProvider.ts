import { PluginInitializationError, PluginRegistrationError, PluginStateError, PluginValidationError } from '../errors/PluginErrors';
import { type IPlugin, type PluginId, createPlugin } from '../models/plugin';
import { PluginState, type PluginStateValue } from '../models/plugin-state';
import {
  PluginRuntimeState,
  type PluginRuntimeDiagnostics,
  type PluginRuntimeHealth,
  type PluginRuntimeStatistics,
  type PluginRuntimeStatus,
  type PluginRuntimeStateValue,
} from '../models/plugin-runtime';
import type { IPluginProvider, PluginRegistrationResult, PluginRuntimeLifecycleResult, PluginUnregistrationResult } from '../interfaces/plugin-provider';
import { PluginDiscoveryManager } from '../runtime/PluginDiscoveryManager';
import type { IPluginDiscoveryManager } from '../interfaces/plugin-discovery';
import { PluginDependencyResolver } from '../runtime/PluginDependencyResolver';
import type { IPluginDependencyResolver } from '../interfaces/plugin-dependency';

export class PluginProvider implements IPluginProvider {
  private runtimeState: PluginRuntimeStateValue = PluginRuntimeState.UNINITIALIZED;
  private readonly plugins = new Map<PluginId, IPlugin>();
  private readonly pluginStates = new Map<PluginId, PluginStateValue>();
  private readonly discoveryManager: IPluginDiscoveryManager = new PluginDiscoveryManager();
  private readonly dependencyResolver: IPluginDependencyResolver = new PluginDependencyResolver(this.discoveryManager);
  private initializationCount = 0;
  private shutdownCount = 0;
  private errorCount = 0;
  private startedAt = 0;

  constructor() {
    this.startedAt = Date.now();
  }

  initialize(): PluginRuntimeLifecycleResult {
    if (this.runtimeState === PluginRuntimeState.READY) {
      return this.freezeLifecycleResult(PluginRuntimeState.READY, true, 'Runtime already ready');
    }

    if (this.runtimeState === PluginRuntimeState.INITIALIZING) {
      return this.freezeLifecycleResult(PluginRuntimeState.INITIALIZING, true, 'Runtime already initializing');
    }

    if (this.runtimeState === PluginRuntimeState.STOPPING || this.runtimeState === PluginRuntimeState.STOPPED) {
      return this.freezeLifecycleResult(this.runtimeState, false, `Invalid transition from ${this.runtimeState}`);
    }

    this.runtimeState = PluginRuntimeState.INITIALIZING;
    this.runtimeState = PluginRuntimeState.READY;
    this.initializationCount += 1;

    return this.freezeLifecycleResult(PluginRuntimeState.READY, true, 'Runtime initialized');
  }

  shutdown(): PluginRuntimeLifecycleResult {
    if (this.runtimeState === PluginRuntimeState.UNINITIALIZED) {
      return this.freezeLifecycleResult(PluginRuntimeState.UNINITIALIZED, false, 'Runtime not initialized');
    }

    if (this.runtimeState === PluginRuntimeState.STOPPED) {
      return this.freezeLifecycleResult(PluginRuntimeState.STOPPED, true, 'Runtime already stopped');
    }

    if (this.runtimeState === PluginRuntimeState.STOPPING) {
      return this.freezeLifecycleResult(PluginRuntimeState.STOPPING, true, 'Runtime already stopping');
    }

    if (this.runtimeState === PluginRuntimeState.ERROR) {
      return this.freezeLifecycleResult(PluginRuntimeState.ERROR, false, 'Runtime is in error state');
    }

    this.runtimeState = PluginRuntimeState.STOPPING;
    this.runtimeState = PluginRuntimeState.STOPPED;
    this.shutdownCount += 1;

    return this.freezeLifecycleResult(PluginRuntimeState.STOPPED, true, 'Runtime stopped');
  }

  state(): PluginRuntimeStateValue {
    return this.runtimeState;
  }

  status(): PluginRuntimeStatus {
    return this.freezeStatus({ state: this.runtimeState, healthy: this.runtimeState === PluginRuntimeState.READY, message: this.runtimeState === PluginRuntimeState.READY ? 'Runtime ready' : 'Runtime not ready' });
  }

  statistics(): PluginRuntimeStatistics {
    const registeredPlugins = this.plugins.size;
    const enabledPlugins = Array.from(this.plugins.values()).filter((plugin) => plugin.enabled).length;
    const disabledPlugins = registeredPlugins - enabledPlugins;

    return Object.freeze({
      registeredPlugins,
      enabledPlugins,
      disabledPlugins,
      initializationCount: this.initializationCount,
      shutdownCount: this.shutdownCount,
      errors: this.errorCount,
      uptime: Math.max(0, Date.now() - this.startedAt),
    });
  }

  health(): PluginRuntimeHealth {
    const stats = this.statistics();
    return Object.freeze({
      healthy: this.runtimeState === PluginRuntimeState.READY,
      state: this.runtimeState,
      registeredPluginCount: stats.registeredPlugins,
      enabledPluginCount: stats.enabledPlugins,
      errorCount: stats.errors,
      message: this.runtimeState === PluginRuntimeState.READY ? 'Runtime healthy' : 'Runtime not healthy',
    });
  }

  registerPlugin(plugin: IPlugin): PluginRegistrationResult {
    this.validatePlugin(plugin);

    if (this.plugins.has(plugin.id)) {
      this.errorCount += 1;
      throw new PluginRegistrationError(`Plugin '${plugin.id}' is already registered`);
    }

    const registeredPlugin = createPlugin({
      ...plugin,
      state: PluginState.REGISTERED,
    });

    this.plugins.set(registeredPlugin.id, registeredPlugin);
    this.pluginStates.set(registeredPlugin.id, registeredPlugin.state);

    return Object.freeze({
      success: true,
      plugin: registeredPlugin,
      pluginId: registeredPlugin.id,
      message: `Plugin '${registeredPlugin.id}' registered`,
    });
  }

  unregisterPlugin(pluginId: PluginId): PluginUnregistrationResult {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) {
      this.errorCount += 1;
      throw new PluginStateError(`Plugin '${pluginId}' does not exist`);
    }

    if (plugin.state !== PluginState.REGISTERED) {
      this.errorCount += 1;
      throw new PluginStateError(`Plugin '${pluginId}' is not in a registrable state`);
    }

    this.plugins.delete(pluginId);
    this.pluginStates.delete(pluginId);

    return Object.freeze({
      success: true,
      pluginId,
      plugin,
      message: `Plugin '${pluginId}' unregistered`,
    });
  }

  hasPlugin(pluginId: PluginId): boolean {
    return this.plugins.has(pluginId);
  }

  getPlugin(pluginId: PluginId): IPlugin | null {
    const plugin = this.plugins.get(pluginId);
    return plugin ? Object.freeze({ ...plugin }) : null;
  }

  listPlugins(): IPlugin[] {
    return Array.from(this.plugins.values()).map((plugin) => Object.freeze({ ...plugin }));
  }

  diagnostics(): PluginRuntimeDiagnostics {
    const statistics = this.statistics();
    const health = this.health();

    return Object.freeze({
      runtimeState: this.runtimeState,
      pluginCounts: Object.freeze({
        registered: statistics.registeredPlugins,
        enabled: statistics.enabledPlugins,
        disabled: statistics.disabledPlugins,
      }),
      statistics: Object.freeze(statistics),
      health: Object.freeze(health),
      capabilities: Object.freeze([]),
    });
  }

  private validatePlugin(plugin: IPlugin): void {
    if (!plugin.id || !plugin.name || !plugin.version) {
      throw new PluginValidationError('Plugin id, name, and version are required');
    }

    if (!plugin.id.trim()) {
      throw new PluginValidationError('Plugin id cannot be empty');
    }

    if (plugin.id.includes(' ')) {
      throw new PluginValidationError('Plugin id cannot contain spaces');
    }

    if (plugin.name.trim().length === 0) {
      throw new PluginValidationError('Plugin name cannot be empty');
    }

    if (plugin.version.trim().length === 0) {
      throw new PluginValidationError('Plugin version cannot be empty');
    }

    if (this.runtimeState !== PluginRuntimeState.READY) {
      throw new PluginInitializationError('Runtime must be initialized before registering plugins');
    }
  }

  private freezeStatus(status: PluginRuntimeStatus): PluginRuntimeStatus {
    return Object.freeze(status);
  }

  private freezeLifecycleResult(state: PluginRuntimeStateValue, healthy: boolean, message: string): PluginRuntimeLifecycleResult {
    return Object.freeze({ state, healthy, message });
  }

  public discovery(): IPluginDiscoveryManager {
    return this.discoveryManager;
  }

  public resolver(): IPluginDependencyResolver {
    return this.dependencyResolver;
  }
}
