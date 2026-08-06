/**
 * Event & Messaging Runtime Domain Models (Phase 16.4.2).
 *
 * Provides immutable state models, event objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, diagnostics
 * telemetry, priority enums, configuration objects, event registration definitions,
 * published event records, and event bus statistics for the Frontend Event Runtime.
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

export interface EventRegistration {
  readonly eventType: string;
  readonly description?: string;
  readonly priority: EventPriority;
  readonly registeredAt: string;
}

export interface PublishedEvent<T = unknown> {
  readonly event: FrontendEvent<T>;
  readonly publishedAt: string;
  readonly sequenceNumber: number;
}

export interface EventHistory {
  readonly events: ReadonlyArray<PublishedEvent>;
  readonly totalPublished: number;
  readonly timestamp: string;
}

export interface EventBusStatistics {
  readonly publishCount: number;
  readonly historyCount: number;
  readonly failedPublishes: number;
  readonly averagePayloadSize: number;
}

export interface EventBusHealth {
  readonly healthy: boolean;
  readonly registeredEventTypes: number;
  readonly totalPublishedEvents: number;
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
  readonly registeredEvents?: ReadonlyArray<string>;
  readonly publishedEvents?: number;
  readonly eventHistorySize?: number;
  readonly busStatistics?: EventBusStatistics;
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

export function createEventRegistration(
  params: Partial<EventRegistration> & { eventType: string },
): EventRegistration {
  return Object.freeze({
    eventType: params.eventType,
    description: params.description,
    priority: params.priority ?? EventPriority.NORMAL,
    registeredAt: params.registeredAt ?? new Date().toISOString(),
  });
}

export function createPublishedEvent<T = unknown>(
  params: Partial<PublishedEvent<T>> & { event: FrontendEvent<T>; sequenceNumber: number },
): PublishedEvent<T> {
  return Object.freeze({
    event: params.event,
    publishedAt: params.publishedAt ?? new Date().toISOString(),
    sequenceNumber: params.sequenceNumber,
  });
}

export function createEventHistory(params: Partial<EventHistory> = {}): EventHistory {
  return Object.freeze({
    events: Object.freeze([...(params.events ?? [])]),
    totalPublished: params.totalPublished ?? (params.events ? params.events.length : 0),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createEventBusStatistics(params: Partial<EventBusStatistics> = {}): EventBusStatistics {
  return Object.freeze({
    publishCount: params.publishCount ?? 0,
    historyCount: params.historyCount ?? 0,
    failedPublishes: params.failedPublishes ?? 0,
    averagePayloadSize: params.averagePayloadSize ?? 0,
  });
}

export function createEventBusHealth(params: Partial<EventBusHealth> = {}): EventBusHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    registeredEventTypes: params.registeredEventTypes ?? 0,
    totalPublishedEvents: params.totalPublishedEvents ?? 0,
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
    registeredEvents: params.registeredEvents ? Object.freeze([...params.registeredEvents]) : undefined,
    publishedEvents: params.publishedEvents,
    eventHistorySize: params.eventHistorySize,
    busStatistics: params.busStatistics,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
