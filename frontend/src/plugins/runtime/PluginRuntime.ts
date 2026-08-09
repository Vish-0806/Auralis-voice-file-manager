import type { IPluginProvider, PluginRegistrationResult, PluginUnregistrationResult } from '../interfaces/plugin-provider';
import type { IPlugin, PluginId } from '../models/plugin';
import type { PluginRuntimeDiagnostics, PluginRuntimeHealth, PluginRuntimeStatistics, PluginRuntimeStatus, PluginRuntimeStateValue } from '../models/plugin-runtime';
import { PluginProvider } from '../provider/PluginProvider';
import type { IPluginDiscoveryManager } from '../interfaces/plugin-discovery';
import type { IPluginDependencyResolver } from '../interfaces/plugin-dependency';
import type { IPluginLoader } from '../interfaces/plugin-loader';
import type { IPluginLifecycleManager } from '../interfaces/plugin-lifecycle';
import type { IPluginCapabilityManager, IPluginExtensionManager } from '../interfaces/plugin-capability';
import type { IPluginSecurityManager, IPluginSandboxManager } from '../interfaces/plugin-security';
import { PluginPolicyManager } from './PluginPolicyManager';

export class PluginRuntime {
  constructor(private readonly runtimeProvider: IPluginProvider = new PluginProvider()) {}

  initialize() {
    return this.runtimeProvider.initialize();
  }

  shutdown() {
    return this.runtimeProvider.shutdown();
  }

  state(): PluginRuntimeStateValue {
    return this.runtimeProvider.state();
  }

  status(): PluginRuntimeStatus {
    return this.runtimeProvider.status();
  }

  statistics(): PluginRuntimeStatistics {
    return this.runtimeProvider.statistics();
  }

  health(): PluginRuntimeHealth {
    return this.runtimeProvider.health();
  }

  registerPlugin(plugin: IPlugin): PluginRegistrationResult {
    return this.runtimeProvider.registerPlugin(plugin);
  }

  unregisterPlugin(pluginId: PluginId): PluginUnregistrationResult {
    return this.runtimeProvider.unregisterPlugin(pluginId);
  }

  hasPlugin(pluginId: PluginId): boolean {
    return this.runtimeProvider.hasPlugin(pluginId);
  }

  getPlugin(pluginId: PluginId): IPlugin | null {
    return this.runtimeProvider.getPlugin(pluginId);
  }

  listPlugins(): IPlugin[] {
    return this.runtimeProvider.listPlugins();
  }

  diagnostics(): PluginRuntimeDiagnostics {
    return this.runtimeProvider.diagnostics();
  }

  provider(): IPluginProvider {
    return this.runtimeProvider;
  }

  public discovery(): IPluginDiscoveryManager {
    return this.runtimeProvider.discovery();
  }

  public resolver(): IPluginDependencyResolver {
    return this.runtimeProvider.resolver();
  }

  public loader(): IPluginLoader {
    return this.runtimeProvider.loader();
  }

  public lifecycle(): IPluginLifecycleManager {
    return this.runtimeProvider.lifecycle();
  }

  public capabilities(): IPluginCapabilityManager {
    return this.runtimeProvider.capabilities();
  }

  public extensions(): IPluginExtensionManager {
    return this.runtimeProvider.extensions();
  }

  public security(): IPluginSecurityManager {
    return this.runtimeProvider.security();
  }

  public policies(): PluginPolicyManager {
    return this.runtimeProvider.policies();
  }

  public sandbox(): IPluginSandboxManager {
    return this.runtimeProvider.sandbox();
  }
}
