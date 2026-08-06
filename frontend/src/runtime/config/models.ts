/**
 * Configuration Runtime Domain Models (Phase 16.3.1).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, and diagnostics
 * telemetry for the Frontend Configuration Runtime.
 */

export enum ConfigurationRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export interface ConfigurationState {
  readonly runtimeState: ConfigurationRuntimeState;
  readonly initialized: boolean;
  readonly startedAt: string | null;
}

export interface ConfigurationCapabilities {
  readonly supportsProfiles: boolean;
  readonly supportsSources: boolean;
  readonly supportsValidation: boolean;
  readonly supportsSecrets: boolean;
  readonly supportsFeatureFlags: boolean;
  readonly supportsDiagnostics: boolean;
}

export interface ConfigurationHealth {
  readonly healthy: boolean;
  readonly runtimeState: ConfigurationRuntimeState;
  readonly message: string;
}

export interface ConfigurationStatistics {
  readonly initializations: number;
  readonly shutdowns: number;
  readonly restarts: number;
  readonly errors: number;
  readonly uptime: number;
}

export interface ConfigurationContext {
  readonly runtimeId: string;
  readonly createdAt: string;
  readonly environment: string;
}

export interface ConfigurationConfiguration {
  readonly runtimeName: string;
  readonly version: string;
  readonly strictMode: boolean;
}

export interface ConfigurationDiagnostics {
  readonly health: ConfigurationHealth;
  readonly statistics: ConfigurationStatistics;
  readonly capabilities: ConfigurationCapabilities;
  readonly context: ConfigurationContext;
  readonly timestamp: string;
}

export function createConfigurationState(
  params: Partial<ConfigurationState> = {},
): ConfigurationState {
  return Object.freeze({
    runtimeState: params.runtimeState ?? ConfigurationRuntimeState.UNINITIALIZED,
    initialized: params.initialized ?? false,
    startedAt: params.startedAt ?? null,
  });
}

export function createConfigurationCapabilities(
  params: Partial<ConfigurationCapabilities> = {},
): ConfigurationCapabilities {
  return Object.freeze({
    supportsProfiles: params.supportsProfiles ?? true,
    supportsSources: params.supportsSources ?? true,
    supportsValidation: params.supportsValidation ?? true,
    supportsSecrets: params.supportsSecrets ?? true,
    supportsFeatureFlags: params.supportsFeatureFlags ?? true,
    supportsDiagnostics: params.supportsDiagnostics ?? true,
  });
}

export function createConfigurationHealth(
  params: Partial<ConfigurationHealth> = {},
): ConfigurationHealth {
  return Object.freeze({
    healthy: params.healthy ?? false,
    runtimeState: params.runtimeState ?? ConfigurationRuntimeState.UNINITIALIZED,
    message: params.message ?? 'Configuration runtime is uninitialized.',
  });
}

export function createConfigurationStatistics(
  params: Partial<ConfigurationStatistics> = {},
): ConfigurationStatistics {
  return Object.freeze({
    initializations: params.initializations ?? 0,
    shutdowns: params.shutdowns ?? 0,
    restarts: params.restarts ?? 0,
    errors: params.errors ?? 0,
    uptime: params.uptime ?? 0,
  });
}

export function createConfigurationContext(
  params: Partial<ConfigurationContext> = {},
): ConfigurationContext {
  return Object.freeze({
    runtimeId: params.runtimeId ?? `config_runtime_${Date.now()}`,
    createdAt: params.createdAt ?? new Date().toISOString(),
    environment: params.environment ?? 'production',
  });
}

export function createConfigurationConfiguration(
  params: Partial<ConfigurationConfiguration> = {},
): ConfigurationConfiguration {
  return Object.freeze({
    runtimeName: params.runtimeName ?? 'Auralis Configuration Runtime',
    version: params.version ?? '1.0.0',
    strictMode: params.strictMode ?? true,
  });
}

export function createConfigurationDiagnostics(
  params: Partial<ConfigurationDiagnostics> = {},
): ConfigurationDiagnostics {
  return Object.freeze({
    health: params.health ?? createConfigurationHealth(),
    statistics: params.statistics ?? createConfigurationStatistics(),
    capabilities: params.capabilities ?? createConfigurationCapabilities(),
    context: params.context ?? createConfigurationContext(),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
