import { freezeDeepSafe } from './dependency';
import type { PluginStateValue } from './plugin-state';

export const PluginIntegrationPhase = {
  DISCOVERY: 'DISCOVERY',
  VALIDATION: 'VALIDATION',
  DEPENDENCY_RESOLUTION: 'DEPENDENCY_RESOLUTION',
  SECURITY_PREFLIGHT: 'SECURITY_PREFLIGHT',
  CONFIGURATION_INITIALIZATION: 'CONFIGURATION_INITIALIZATION',
  LOADING: 'LOADING',
  SANDBOX_INITIALIZATION: 'SANDBOX_INITIALIZATION',
  LIFECYCLE_INITIALIZATION: 'LIFECYCLE_INITIALIZATION',
  CAPABILITY_REGISTRATION: 'CAPABILITY_REGISTRATION',
  ACTIVATION: 'ACTIVATION',
  READY: 'READY',
  DEACTIVATION: 'DEACTIVATION',
  CLEANUP: 'CLEANUP',
  UNLOADING: 'UNLOADING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED'
} as const;

export type PluginIntegrationPhaseValue = typeof PluginIntegrationPhase[keyof typeof PluginIntegrationPhase];

export interface PluginIntegrationOptions {
  readonly skipOptionalDependencies?: boolean;
  readonly allowSensitiveConfig?: boolean;
  readonly forceReload?: boolean;
}

export interface PluginIntegrationResult {
  readonly pluginId: string;
  readonly success: boolean;
  readonly phase: PluginIntegrationPhaseValue;
  readonly currentState: PluginStateValue;
  readonly timestamp: number;
  readonly duration: number;
  readonly errors: ReadonlyArray<{ readonly message: string; readonly stack?: string }>;
  readonly warnings: ReadonlyArray<string>;
  readonly skipped: ReadonlyArray<string>;
  readonly sandboxStatus?: string;
  readonly configurationStatus?: string;
  readonly capabilitiesRegistered: ReadonlyArray<string>;
  readonly extensionsRegistered: ReadonlyArray<string>;
}

export interface PluginIntegrationRecord {
  readonly integrationId: string;
  readonly pluginId: string;
  readonly success: boolean;
  readonly startedAt: number;
  readonly completedAt: number;
  readonly duration: number;
  readonly finalPhase: PluginIntegrationPhaseValue;
  readonly errors: ReadonlyArray<{ readonly message: string; readonly stack?: string }>;
  readonly rollbacks: ReadonlyArray<string>;
}

export interface PluginIntegrationStatistics {
  readonly totalAttempts: number;
  readonly successfulIntegrations: number;
  readonly failedIntegrations: number;
  readonly rolledBackIntegrations: number;
  readonly currentlyIntegrating: number;
  readonly readyPlugins: number;
  readonly failedPlugins: number;
  readonly averageDuration: number;
  readonly maxDuration: number;
  readonly minDuration: number;
  readonly startupDuration: number;
  readonly shutdownDuration: number;
  readonly reloadCount: number;
  readonly dependencyFailures: number;
  readonly securityRejections: number;
  readonly configurationFailures: number;
  readonly loadingFailures: number;
  readonly lifecycleFailures: number;
  readonly capabilityFailures: number;
  readonly sandboxFailures: number;
}

export interface PluginIntegrationHealth {
  readonly healthy: boolean;
  readonly readyPluginCount: number;
  readonly failedIntegrationCount: number;
  readonly securityRejectionCount: number;
  readonly dependencyFailureCount: number;
  readonly activeIntegrationCount: number;
  readonly rollbackCount: number;
  readonly failureRate: number;
  readonly message: string;
}

export interface PluginIntegrationDiagnostics {
  readonly statistics: PluginIntegrationStatistics;
  readonly health: PluginIntegrationHealth;
  readonly activeIntegrations: ReadonlyArray<string>;
  readonly historyDepth: number;
  readonly lastIntegrationRecord?: PluginIntegrationRecord;
}

// Factories
export function createPluginIntegrationResult(input: PluginIntegrationResult): PluginIntegrationResult {
  return freezeDeepSafe(input);
}

export function createPluginIntegrationRecord(input: PluginIntegrationRecord): PluginIntegrationRecord {
  return freezeDeepSafe(input);
}

export function createPluginIntegrationStatistics(input: PluginIntegrationStatistics): PluginIntegrationStatistics {
  return freezeDeepSafe(input);
}

export function createPluginIntegrationHealth(input: PluginIntegrationHealth): PluginIntegrationHealth {
  return freezeDeepSafe(input);
}

export function createPluginIntegrationDiagnostics(input: PluginIntegrationDiagnostics): PluginIntegrationDiagnostics {
  return freezeDeepSafe(input);
}
