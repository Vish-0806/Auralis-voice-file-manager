/**
 * Configuration Runtime Domain Models (Phase 16.3.2).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, diagnostics
 * telemetry, source priority enums, entry records, and snapshots for the Frontend Configuration Runtime.
 */

export enum ConfigurationRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export enum ConfigurationSourcePriority {
  MEMORY = 500,
  RUNTIME = 400,
  ENVIRONMENT = 300,
  LOCAL = 200,
  SESSION = 100,
  DEFAULT = 0,
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

export interface ConfigurationEntry {
  readonly key: string;
  readonly value: unknown;
  readonly sourceName: string;
  readonly priority: number;
  readonly timestamp: string;
}

export interface ConfigurationSnapshot {
  readonly entries: Readonly<Record<string, ConfigurationEntry>>;
  readonly mergedValues: Readonly<Record<string, unknown>>;
  readonly timestamp: string;
  readonly sourceCount: number;
}

export interface ConfigurationSourceStatistics {
  readonly reads: number;
  readonly writes: number;
  readonly deletes: number;
  readonly hits: number;
  readonly misses: number;
  readonly itemCount: number;
}

export interface ConfigurationSourceHealth {
  readonly healthy: boolean;
  readonly sourceName: string;
  readonly enabled: boolean;
  readonly message: string;
}

export interface ConfigurationSourceRegistration {
  readonly sourceName: string;
  readonly priority: number;
  readonly enabled: boolean;
  readonly registeredAt: string;
}

export interface ConfigurationDiagnostics {
  readonly health: ConfigurationHealth;
  readonly statistics: ConfigurationStatistics;
  readonly capabilities: ConfigurationCapabilities;
  readonly context: ConfigurationContext;
  readonly sources?: ReadonlyArray<ConfigurationSourceRegistration>;
  readonly snapshot?: ConfigurationSnapshot;
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

export function createConfigurationEntry(
  params: Partial<ConfigurationEntry> & { key: string; value: unknown; sourceName: string },
): ConfigurationEntry {
  return Object.freeze({
    key: params.key,
    value: params.value,
    sourceName: params.sourceName,
    priority: params.priority ?? ConfigurationSourcePriority.DEFAULT,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createConfigurationSnapshot(
  params: Partial<ConfigurationSnapshot> = {},
): ConfigurationSnapshot {
  return Object.freeze({
    entries: Object.freeze({ ...(params.entries ?? {}) }),
    mergedValues: Object.freeze({ ...(params.mergedValues ?? {}) }),
    timestamp: params.timestamp ?? new Date().toISOString(),
    sourceCount: params.sourceCount ?? 0,
  });
}

export function createConfigurationSourceStatistics(
  params: Partial<ConfigurationSourceStatistics> = {},
): ConfigurationSourceStatistics {
  return Object.freeze({
    reads: params.reads ?? 0,
    writes: params.writes ?? 0,
    deletes: params.deletes ?? 0,
    hits: params.hits ?? 0,
    misses: params.misses ?? 0,
    itemCount: params.itemCount ?? 0,
  });
}

export function createConfigurationSourceHealth(
  params: Partial<ConfigurationSourceHealth> & { sourceName: string },
): ConfigurationSourceHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    sourceName: params.sourceName,
    enabled: params.enabled ?? true,
    message: params.message ?? `Source '${params.sourceName}' is operational.`,
  });
}

export function createConfigurationSourceRegistration(
  params: Partial<ConfigurationSourceRegistration> & { sourceName: string },
): ConfigurationSourceRegistration {
  return Object.freeze({
    sourceName: params.sourceName,
    priority: params.priority ?? ConfigurationSourcePriority.DEFAULT,
    enabled: params.enabled ?? true,
    registeredAt: params.registeredAt ?? new Date().toISOString(),
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
    sources: params.sources ? Object.freeze([...params.sources]) : undefined,
    snapshot: params.snapshot,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
