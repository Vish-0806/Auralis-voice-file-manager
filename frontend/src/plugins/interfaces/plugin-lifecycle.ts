import type { PluginStateValue } from '../models/plugin-state';
import type {
  PluginLifecycleHookContext,
  PluginLifecycleResult,
  PluginLifecycleRecord,
  PluginLifecycleStatistics,
  PluginLifecycleHealth,
  PluginLifecycleDiagnostics
} from '../models/lifecycle';

export type PluginLifecycleHook = (context: PluginLifecycleHookContext) => void | Promise<void>;

export interface PluginLifecycleHooks {
  readonly onInitialize?: PluginLifecycleHook;
  readonly onActivate?: PluginLifecycleHook;
  readonly onDeactivate?: PluginLifecycleHook;
  readonly onDispose?: PluginLifecycleHook;
}

export interface IPluginLifecycleManager {
  initializePlugin(pluginId: string): Promise<PluginLifecycleResult>;
  activatePlugin(pluginId: string): Promise<PluginLifecycleResult>;
  deactivatePlugin(pluginId: string): Promise<PluginLifecycleResult>;
  disposePlugin(pluginId: string): Promise<PluginLifecycleResult>;
  
  initializeAll(): Promise<ReadonlyArray<PluginLifecycleResult>>;
  activateAll(): Promise<ReadonlyArray<PluginLifecycleResult>>;
  deactivateAll(): Promise<ReadonlyArray<PluginLifecycleResult>>;
  disposeAll(): Promise<ReadonlyArray<PluginLifecycleResult>>;
  
  getLifecycleState(pluginId: string): PluginStateValue;
  registerHooks(pluginId: string, hooks: PluginLifecycleHooks): void;
  unregisterHooks(pluginId: string): void;
  
  history(): ReadonlyArray<PluginLifecycleRecord>;
  clearHistory(): void;
  statistics(): PluginLifecycleStatistics;
  health(): PluginLifecycleHealth;
  diagnostics(): PluginLifecycleDiagnostics;
  reset(): void;
}
