import { freezeDeepSafe } from './dependency';

export const PluginLoadStatus = {
  NOT_LOADED: 'NOT_LOADED',
  LOADING: 'LOADING',
  LOADED: 'LOADED',
  FAILED: 'FAILED',
  UNLOADING: 'UNLOADING',
  UNLOADED: 'UNLOADED'
} as const;
export type PluginLoadStatusValue = typeof PluginLoadStatus[keyof typeof PluginLoadStatus];

export interface PluginModule {
  readonly pluginId: string;
  readonly version: string;
  readonly entryPoint: string;
  readonly loadedAt: number;
  readonly module: unknown;
}

export interface PluginLoadRequest {
  readonly pluginId: string;
  readonly force?: boolean;
}

export interface PluginLoadResult {
  readonly pluginId: string;
  readonly status: PluginLoadStatusValue;
  readonly success: boolean;
  readonly loadDuration: number;
  readonly error?: {
    readonly message: string;
    readonly stack?: string;
  };
  readonly warnings: ReadonlyArray<string>;
  readonly resolvedEntryPoint?: string;
  readonly timestamp: number;
}

export interface PluginLoadRecord {
  readonly pluginId: string;
  readonly status: PluginLoadStatusValue;
  readonly startedAt: number;
  readonly completedAt: number;
  readonly duration: number;
  readonly success: boolean;
  readonly error?: {
    readonly message: string;
  };
}

export interface PluginLoaderStatistics {
  readonly loadAttempts: number;
  readonly successfulLoads: number;
  readonly failedLoads: number;
  readonly unloadAttempts: number;
  readonly successfulUnloads: number;
  readonly failedUnloads: number;
  readonly duplicateLoadAttempts: number;
  readonly activeLoadedPlugins: number;
  readonly averageLoadTime: number;
  readonly maximumLoadTime: number;
  readonly minimumLoadTime: number;
}

export interface PluginLoaderHealth {
  readonly healthy: boolean;
  readonly loadedPlugins: number;
  readonly failedPlugins: number;
  readonly activeLoads: number;
  readonly failureRate: number;
  readonly message: string;
}

export function createLoadResult(input: Omit<PluginLoadResult, typeof Symbol.toStringTag>): PluginLoadResult {
  return freezeDeepSafe(input);
}
