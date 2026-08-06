/**
 * Frontend Runtime Domain Models (Phase 16.1).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, and diagnostics telemetry.
 */

export enum FrontendRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  RUNNING = 'RUNNING',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export interface FrontendState {
  readonly status: FrontendRuntimeState;
  readonly initialized: boolean;
  readonly startTime: string | null;
  readonly restartCount: number;
  readonly errorCount: number;
  readonly lastError: string | null;
}

export interface FrontendConfiguration {
  readonly appName: string;
  readonly environment: string;
  readonly version: string;
  readonly debug: boolean;
  readonly maxRetries: number;
  readonly timeoutMs: number;
}

export interface FrontendCapabilities {
  readonly offlineSupport: boolean;
  readonly realTimeSync: boolean;
  readonly storageQuotaMb: number;
  readonly maxConcurrentOperations: number;
  readonly customFeatures: Readonly<Record<string, boolean>>;
}

export interface FrontendHealth {
  readonly healthy: boolean;
  readonly status: FrontendRuntimeState;
  readonly details: Readonly<Record<string, unknown>>;
  readonly timestamp: string;
}

export interface FrontendStatistics {
  readonly initializations: number;
  readonly shutdowns: number;
  readonly restarts: number;
  readonly totalOperations: number;
  readonly failedOperations: number;
  readonly uptimeSeconds: number;
}

export interface FrontendContext {
  readonly appId: string;
  readonly environment: string;
  readonly version: string;
  readonly sessionKey: string;
}

export interface FrontendDiagnostics {
  readonly state: FrontendState;
  readonly health: FrontendHealth;
  readonly statistics: FrontendStatistics;
  readonly capabilities: FrontendCapabilities;
  readonly context: FrontendContext;
  readonly timestamp: string;
}

export function createFrontendState(params: Partial<FrontendState> = {}): FrontendState {
  return Object.freeze({
    status: params.status ?? FrontendRuntimeState.UNINITIALIZED,
    initialized: params.initialized ?? false,
    startTime: params.startTime ?? null,
    restartCount: params.restartCount ?? 0,
    errorCount: params.errorCount ?? 0,
    lastError: params.lastError ?? null,
  });
}

export function createFrontendConfiguration(
  params: Partial<FrontendConfiguration> = {},
): FrontendConfiguration {
  return Object.freeze({
    appName: params.appName ?? 'Auralis Frontend',
    environment: params.environment ?? 'production',
    version: params.version ?? '1.0.0',
    debug: params.debug ?? false,
    maxRetries: params.maxRetries ?? 3,
    timeoutMs: params.timeoutMs ?? 5000,
  });
}

export function createFrontendCapabilities(
  params: Partial<FrontendCapabilities> = {},
): FrontendCapabilities {
  return Object.freeze({
    offlineSupport: params.offlineSupport ?? true,
    realTimeSync: params.realTimeSync ?? true,
    storageQuotaMb: params.storageQuotaMb ?? 50,
    maxConcurrentOperations: params.maxConcurrentOperations ?? 10,
    customFeatures: Object.freeze({ ...(params.customFeatures ?? {}) }),
  });
}

export function createFrontendHealth(params: Partial<FrontendHealth> = {}): FrontendHealth {
  return Object.freeze({
    healthy: params.healthy ?? false,
    status: params.status ?? FrontendRuntimeState.UNINITIALIZED,
    details: Object.freeze({ ...(params.details ?? {}) }),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createFrontendStatistics(
  params: Partial<FrontendStatistics> = {},
): FrontendStatistics {
  return Object.freeze({
    initializations: params.initializations ?? 0,
    shutdowns: params.shutdowns ?? 0,
    restarts: params.restarts ?? 0,
    totalOperations: params.totalOperations ?? 0,
    failedOperations: params.failedOperations ?? 0,
    uptimeSeconds: params.uptimeSeconds ?? 0,
  });
}

export function createFrontendContext(params: Partial<FrontendContext> = {}): FrontendContext {
  return Object.freeze({
    appId: params.appId ?? 'auralis-frontend',
    environment: params.environment ?? 'production',
    version: params.version ?? '1.0.0',
    sessionKey: params.sessionKey ?? 'default-session',
  });
}

export function createFrontendDiagnostics(
  params: Partial<FrontendDiagnostics> = {},
): FrontendDiagnostics {
  return Object.freeze({
    state: params.state ?? createFrontendState(),
    health: params.health ?? createFrontendHealth(),
    statistics: params.statistics ?? createFrontendStatistics(),
    capabilities: params.capabilities ?? createFrontendCapabilities(),
    context: params.context ?? createFrontendContext(),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
