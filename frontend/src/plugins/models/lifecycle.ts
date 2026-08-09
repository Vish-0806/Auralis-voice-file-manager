import type { PluginStateValue } from './plugin-state';
import { freezeDeepSafe } from './dependency';

export const PluginLifecycleOperation = {
  INITIALIZE: 'initialize',
  ACTIVATE: 'activate',
  DEACTIVATE: 'deactivate',
  DISPOSE: 'dispose'
} as const;
export type PluginLifecycleOperationValue = typeof PluginLifecycleOperation[keyof typeof PluginLifecycleOperation];

export interface PluginLifecycleHookContext {
  readonly pluginId: string;
  readonly pluginVersion: string;
  readonly currentLifecycleState: PluginStateValue;
  readonly requestedOperation: PluginLifecycleOperationValue;
  readonly timestamp: number;
  readonly executionId: string;
  readonly dependencyInformation: ReadonlyArray<string>;
}

export interface PluginLifecycleResult {
  readonly pluginId: string;
  readonly operation: PluginLifecycleOperationValue;
  readonly previousState: PluginStateValue;
  readonly currentState: PluginStateValue;
  readonly success: boolean;
  readonly duration: number;
  readonly error?: {
    readonly message: string;
    readonly stack?: string;
  };
  readonly warnings: ReadonlyArray<string>;
  readonly timestamp: number;
}

export interface PluginLifecycleRecord {
  readonly executionId: string;
  readonly pluginId: string;
  readonly operation: PluginLifecycleOperationValue;
  readonly previousState: PluginStateValue;
  readonly currentState: PluginStateValue;
  readonly startedAt: number;
  readonly completedAt: number;
  readonly duration: number;
  readonly success: boolean;
  readonly error?: {
    readonly message: string;
  };
}

export interface PluginLifecycleStatistics {
  readonly initializeCount: number;
  readonly activationCount: number;
  readonly deactivationCount: number;
  readonly disposalCount: number;
  readonly successfulOperations: number;
  readonly failedOperations: number;
  readonly activePlugins: number;
  readonly disposedPlugins: number;
  readonly failedPlugins: number;
  readonly averageLifecycleTime: number;
  readonly minimumLifecycleTime: number;
  readonly maximumLifecycleTime: number;
  readonly lifecycleHistorySize: number;
}

export interface PluginLifecycleHealth {
  readonly healthy: boolean;
  readonly successRate: number;
  readonly failureRate: number;
  readonly activePluginCount: number;
  readonly failedPluginCount: number;
  readonly message: string;
}

export interface PluginLifecycleDiagnostics {
  readonly statistics: PluginLifecycleStatistics;
  readonly health: PluginLifecycleHealth;
  readonly currentActivePluginCount: number;
  readonly lifecycleHistoryDepth: number;
  readonly registeredLifecycleHookCount: number;
  readonly lastLifecycleOperationMetadata?: {
    readonly pluginId: string;
    readonly operation: PluginLifecycleOperationValue;
    readonly success: boolean;
    readonly timestamp: number;
  };
}

export function createLifecycleResult(input: Omit<PluginLifecycleResult, typeof Symbol.toStringTag>): PluginLifecycleResult {
  return freezeDeepSafe(input);
}
