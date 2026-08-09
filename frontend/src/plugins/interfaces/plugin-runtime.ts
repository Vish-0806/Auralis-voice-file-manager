import type { IPluginProvider } from './plugin-provider';

export interface IPluginRuntime {
  initialize(): { readonly state: string; readonly healthy: boolean; readonly message: string };
  shutdown(): { readonly state: string; readonly healthy: boolean; readonly message: string };
  state(): string;
  status(): { readonly state: string; readonly healthy: boolean; readonly message: string };
  statistics(): {
    readonly registeredPlugins: number;
    readonly enabledPlugins: number;
    readonly disabledPlugins: number;
    readonly initializationCount: number;
    readonly shutdownCount: number;
    readonly errors: number;
    readonly uptime: number;
  };
  health(): {
    readonly healthy: boolean;
    readonly state: string;
    readonly registeredPluginCount: number;
    readonly enabledPluginCount: number;
    readonly errorCount: number;
    readonly message: string;
  };
  registerPlugin(plugin: { readonly id: string; readonly name: string; readonly version: string; readonly description?: string; readonly author?: string; readonly enabled?: boolean; readonly metadata?: Record<string, unknown>; readonly state?: string }): { readonly success: boolean; readonly plugin: { readonly id: string; readonly name: string; readonly version: string; readonly description?: string; readonly author?: string; readonly enabled: boolean; readonly metadata: Record<string, unknown>; readonly state: string }; readonly pluginId: string; readonly message: string };
  unregisterPlugin(pluginId: string): { readonly success: boolean; readonly pluginId: string; readonly plugin?: { readonly id: string; readonly name: string; readonly version: string; readonly description?: string; readonly author?: string; readonly enabled: boolean; readonly metadata: Record<string, unknown>; readonly state: string }; readonly message: string };
  hasPlugin(pluginId: string): boolean;
  getPlugin(pluginId: string): { readonly id: string; readonly name: string; readonly version: string; readonly description?: string; readonly author?: string; readonly enabled: boolean; readonly metadata: Record<string, unknown>; readonly state: string } | null;
  listPlugins(): Array<{ readonly id: string; readonly name: string; readonly version: string; readonly description?: string; readonly author?: string; readonly enabled: boolean; readonly metadata: Record<string, unknown>; readonly state: string }>;
  diagnostics(): {
    readonly runtimeState: string;
    readonly pluginCounts: {
      readonly registered: number;
      readonly enabled: number;
      readonly disabled: number;
    };
    readonly statistics: {
      readonly registeredPlugins: number;
      readonly enabledPlugins: number;
      readonly disabledPlugins: number;
      readonly initializationCount: number;
      readonly shutdownCount: number;
      readonly errors: number;
      readonly uptime: number;
    };
    readonly health: {
      readonly healthy: boolean;
      readonly state: string;
      readonly registeredPluginCount: number;
      readonly enabledPluginCount: number;
      readonly errorCount: number;
      readonly message: string;
    };
    readonly capabilities: ReadonlyArray<{ readonly id: string; readonly description?: string }>;
  };
  provider(): IPluginProvider;
}
