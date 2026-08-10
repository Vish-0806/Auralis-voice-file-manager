import type { IPlugin, PluginId } from '../models/plugin';
import type {
  PluginRuntimeDiagnostics,
  PluginRuntimeHealth,
  PluginRuntimeStatistics,
  PluginRuntimeStatus,
  PluginRuntimeStateValue,
} from '../models/plugin-runtime';
import type { IPluginDiscoveryManager } from './plugin-discovery';
import type { IPluginDependencyResolver } from './plugin-dependency';
import type { IPluginLoader } from './plugin-loader';
import type { IPluginLifecycleManager } from './plugin-lifecycle';
import type { IPluginCapabilityManager, IPluginExtensionManager } from './plugin-capability';
import type { IPluginSecurityManager, IPluginSandboxManager } from './plugin-security';
import type { IPluginConfigurationManager } from './plugin-configuration';
import { PluginPolicyManager } from '../runtime/PluginPolicyManager';

export interface PluginRuntimeLifecycleResult {
  readonly state: PluginRuntimeStateValue;
  readonly healthy: boolean;
  readonly message: string;
}

export interface PluginRegistrationResult {
  readonly success: boolean;
  readonly plugin: IPlugin;
  readonly pluginId: PluginId;
  readonly message: string;
}

export interface PluginUnregistrationResult {
  readonly success: boolean;
  readonly pluginId: PluginId;
  readonly plugin?: IPlugin;
  readonly message: string;
}

export interface IPluginProvider {
  initialize(): PluginRuntimeLifecycleResult;
  shutdown(): PluginRuntimeLifecycleResult;
  state(): PluginRuntimeStateValue;
  status(): PluginRuntimeStatus;
  statistics(): PluginRuntimeStatistics;
  health(): PluginRuntimeHealth;
  registerPlugin(plugin: IPlugin): PluginRegistrationResult;
  unregisterPlugin(pluginId: PluginId): PluginUnregistrationResult;
  hasPlugin(pluginId: PluginId): boolean;
  getPlugin(pluginId: PluginId): IPlugin | null;
  listPlugins(): IPlugin[];
  diagnostics(): PluginRuntimeDiagnostics;
  discovery(): IPluginDiscoveryManager;
  resolver(): IPluginDependencyResolver;
  loader(): IPluginLoader;
  lifecycle(): IPluginLifecycleManager;
  capabilities(): IPluginCapabilityManager;
  extensions(): IPluginExtensionManager;
  security(): IPluginSecurityManager;
  policies(): PluginPolicyManager;
  sandbox(): IPluginSandboxManager;
  configuration(): IPluginConfigurationManager;
}
