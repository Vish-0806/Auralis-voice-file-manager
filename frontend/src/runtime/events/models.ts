/**
 * Event & Messaging Runtime Domain Models (Phase 16.4.1).
 *
 * Provides immutable state models, event objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, diagnostics
 * telemetry, priority enums, and configuration objects for the Frontend Event Runtime.
 */

export enum EventRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export enum EventPriority {
  LOW = 0,
  NORMAL = 100,
  HIGH = 200,
  CRITICAL = 300,
}

export interface EventState {
  readonly runtimeState: EventRuntimeState;
  readonly initialized: boolean;
  readonly startedAt: string | null;
}

export interface FrontendEvent<T = unknown> {
  readonly eventId: string;
  readonly eventType: string;
  readonly payload: T;
  readonly priority: EventPriority;
  readonly timestamp: string;
  readonly source?: string;
  readonly correlationId?: string;
}

export interface EventContext {
  readonly runtimeId: string;
  readonly createdAt: string;
  readonly environment: string;
}

export interface EventCapabilities {
  readonly supportsEventBus: boolean;
  readonly supportsPubSub: boolean;
  readonly supportsAsyncDispatch: boolean;
  readonly supportsFiltering: boolean;
  readonly supportsDeadLetterQueue: boolean;
  readonly supportsDiagnostics: boolean;
}

export interface EventStatistics {
  readonly initializations: number;
  readonly shutdowns: number;
  readonly restarts: number;
  readonly errors: number;
  readonly uptime: number;
}

export interface EventHealth {
  readonly healthy: boolean;
  readonly runtimeState: EventRuntimeState;
  readonly message: string;
}

export interface EventConfiguration {
  readonly runtimeName: string;
  readonly version: string;
  readonly strictMode: boolean;
  readonly maxQueueSize?: number;
}

export interface EventDiagnostics {
  readonly health: EventHealth;
  readonly statistics: EventStatistics;
  readonly capabilities: EventCapabilities;
  readonly context: EventContext;
  readonly timestamp: string;
}

export function createEventState(params: Partial<EventState> = {}): EventState {
  return Object.freeze({
    runtimeState: params.runtimeState ?? EventRuntimeState.UNINITIALIZED,
    initialized: params.initialized ?? false,
    startedAt: params.startedAt ?? null,
  });
}

export function createFrontendEvent<T = unknown>(
  params: Partial<FrontendEvent<T>> & { eventType: string; payload: T },
): FrontendEvent<T> {
  return Object.freeze({
    eventId: params.eventId ?? `evt_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    eventType: params.eventType,
    payload: params.payload,
    priority: params.priority ?? EventPriority.NORMAL,
    timestamp: params.timestamp ?? new Date().toISOString(),
    source: params.source,
    correlationId: params.correlationId,
  });
}

export function createEventContext(params: Partial<EventContext> = {}): EventContext {
  return Object.freeze({
    runtimeId: params.runtimeId ?? `event_runtime_${Date.now()}`,
    createdAt: params.createdAt ?? new Date().toISOString(),
    environment: params.environment ?? 'production',
  });
}

export function createEventCapabilities(params: Partial<EventCapabilities> = {}): EventCapabilities {
  return Object.freeze({
    supportsEventBus: params.supportsEventBus ?? true,
    supportsPubSub: params.supportsPubSub ?? true,
    supportsAsyncDispatch: params.supportsAsyncDispatch ?? true,
    supportsFiltering: params.supportsFiltering ?? true,
    supportsDeadLetterQueue: params.supportsDeadLetterQueue ?? true,
    supportsDiagnostics: params.supportsDiagnostics ?? true,
  });
}

export function createEventStatistics(params: Partial<EventStatistics> = {}): EventStatistics {
  return Object.freeze({
    initializations: params.initializations ?? 0,
    shutdowns: params.shutdowns ?? 0,
    restarts: params.restarts ?? 0,
    errors: params.errors ?? 0,
    uptime: params.uptime ?? 0,
  });
}

export function createEventHealth(params: Partial<EventHealth> = {}): EventHealth {
  return Object.freeze({
    healthy: params.healthy ?? false,
    runtimeState: params.runtimeState ?? EventRuntimeState.UNINITIALIZED,
    message: params.message ?? 'Event runtime is uninitialized.',
  });
}

export function createEventConfiguration(params: Partial<EventConfiguration> = {}): EventConfiguration {
  return Object.freeze({
    runtimeName: params.runtimeName ?? 'Auralis Event Runtime',
    version: params.version ?? '1.0.0',
    strictMode: params.strictMode ?? true,
    maxQueueSize: params.maxQueueSize ?? 1000,
  });
}

export function createEventDiagnostics(params: Partial<EventDiagnostics> = {}): EventDiagnostics {
  return Object.freeze({
    health: params.health ?? createEventHealth(),
    statistics: params.statistics ?? createEventStatistics(),
    capabilities: params.capabilities ?? createEventCapabilities(),
    context: params.context ?? createEventContext(),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
