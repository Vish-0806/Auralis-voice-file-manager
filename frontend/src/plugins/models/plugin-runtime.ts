import { type PluginCapabilityId } from './plugin';

export const PluginRuntimeState = {
  UNINITIALIZED: 'UNINITIALIZED',
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  STOPPING: 'STOPPING',
  STOPPED: 'STOPPED',
  ERROR: 'ERROR',
} as const;

export type PluginRuntimeStateValue = (typeof PluginRuntimeState)[keyof typeof PluginRuntimeState];

export interface PluginRuntimeStatistics {
  readonly registeredPlugins: number;
  readonly enabledPlugins: number;
  readonly disabledPlugins: number;
  readonly initializationCount: number;
  readonly shutdownCount: number;
  readonly errors: number;
  readonly uptime: number;
}

export interface PluginRuntimeStatus {
  readonly state: PluginRuntimeStateValue;
  readonly healthy: boolean;
  readonly message: string;
}

export interface PluginRuntimeHealth {
  readonly healthy: boolean;
  readonly state: PluginRuntimeStateValue;
  readonly registeredPluginCount: number;
  readonly enabledPluginCount: number;
  readonly errorCount: number;
  readonly message: string;
}

export interface PluginRuntimeDiagnostics {
  readonly runtimeState: PluginRuntimeStateValue;
  readonly pluginCounts: {
    readonly registered: number;
    readonly enabled: number;
    readonly disabled: number;
  };
  readonly statistics: PluginRuntimeStatistics;
  readonly health: PluginRuntimeHealth;
  readonly capabilities: ReadonlyArray<PluginRuntimeCapability>;
  readonly loader?: Record<string, any>;
  readonly lifecycle?: Record<string, any>;
  readonly capabilityManager?: Record<string, any>;
  readonly extensionManager?: Record<string, any>;
}

export interface PluginRuntimeCapability {
  readonly id: PluginCapabilityId;
  readonly description?: string;
}
