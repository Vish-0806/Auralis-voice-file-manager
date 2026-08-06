/**
 * Event & Messaging Runtime Domain Models (Phase 16.4.4).
 *
 * Provides immutable state models, event objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, diagnostics
 * telemetry, priority enums, configuration objects, event registration definitions,
 * published event records, subscriber registrations, execution results, subscriber health,
 * routing rules, routing decisions, dispatch policies, dispatch records, and dead-letter telemetry for the Frontend Event Runtime.
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

export interface EventSubscription {
  readonly subscriptionId: string;
  readonly eventType: string;
  readonly priority: EventPriority;
  readonly subscribedAt: string;
  readonly active: boolean;
}

export interface SubscriberRegistration<T = unknown> {
  readonly subscriptionId: string;
  readonly eventType: string;
  readonly handler: (event: FrontendEvent<T>) => void | Promise<void>;
  readonly priority: EventPriority;
  readonly subscribedAt: string;
  readonly active: boolean;
}

export interface SubscriptionExecution {
  readonly subscriptionId: string;
  readonly eventId: string;
  readonly eventType: string;
  readonly success: boolean;
  readonly durationMs: number;
  readonly error?: string;
  readonly executedAt: string;
}

export interface SubscriptionResult {
  readonly publishedEvent: PublishedEvent;
  readonly executions: ReadonlyArray<SubscriptionExecution>;
  readonly totalExecutions: number;
  readonly successfulExecutions: number;
  readonly failedExecutions: number;
  readonly executedAt: string;
}

export interface SubscriberStatistics {
  readonly totalSubscriptions: number;
  readonly activeSubscriptions: number;
  readonly totalExecutions: number;
  readonly successfulExecutions: number;
  readonly failedExecutions: number;
  readonly averageExecutionMs: number;
}

export interface SubscriberHealth {
  readonly healthy: boolean;
  readonly activeSubscriptionsCount: number;
  readonly totalExecutionsCount: number;
  readonly errorRate: number;
}

export interface RoutingRule {
  readonly ruleId: string;
  readonly name: string;
  readonly topicPattern: string;
  readonly predicate?: (event: FrontendEvent) => boolean;
  readonly priority: EventPriority;
  readonly enabled: boolean;
}

export interface RoutingDecision {
  readonly decisionId: string;
  readonly event: FrontendEvent;
  readonly matchedRules: ReadonlyArray<RoutingRule>;
  readonly matched: boolean;
  readonly evaluatedAt: string;
}

export interface DispatchPolicy {
  readonly policyId: string;
  readonly name: string;
  readonly stopOnFirstFailure: boolean;
  readonly deadLetterEnabled: boolean;
}

export interface DispatchRecord {
  readonly dispatchId: string;
  readonly decision: RoutingDecision;
  readonly executions: ReadonlyArray<SubscriptionExecution>;
  readonly success: boolean;
  readonly totalDurationMs: number;
  readonly dispatchedAt: string;
}

export interface DispatchStatistics {
  readonly totalDispatches: number;
  readonly successfulDispatches: number;
  readonly failedDispatches: number;
  readonly averageDispatchMs: number;
  readonly deadLetterCount: number;
}

export interface DispatchHealth {
  readonly healthy: boolean;
  readonly activeRulesCount: number;
  readonly dispatchErrorRate: number;
}

export interface DeadLetterRecord {
  readonly deadLetterId: string;
  readonly event: FrontendEvent;
  readonly reason: string;
  readonly error?: string;
  readonly failedAt: string;
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
  readonly subscriberCount?: number;
  readonly subscriptionCount?: number;
  readonly subscriberStatistics?: SubscriberStatistics;
  readonly subscriberHealth?: SubscriberHealth;
  readonly routingRules?: ReadonlyArray<string>;
  readonly dispatchStatistics?: DispatchStatistics;
  readonly dispatchHealth?: DispatchHealth;
  readonly deadLetterCount?: number;
  readonly routingEvaluations?: number;
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

export function createEventSubscription(params: Partial<EventSubscription> & { eventType: string }): EventSubscription {
  return Object.freeze({
    subscriptionId: params.subscriptionId ?? `sub_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    eventType: params.eventType,
    priority: params.priority ?? EventPriority.NORMAL,
    subscribedAt: params.subscribedAt ?? new Date().toISOString(),
    active: params.active ?? true,
  });
}

export function createSubscriberRegistration<T = unknown>(
  params: Partial<SubscriberRegistration<T>> & {
    eventType: string;
    handler: (event: FrontendEvent<T>) => void | Promise<void>;
  },
): SubscriberRegistration<T> {
  return Object.freeze({
    subscriptionId: params.subscriptionId ?? `sub_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    eventType: params.eventType,
    handler: params.handler,
    priority: params.priority ?? EventPriority.NORMAL,
    subscribedAt: params.subscribedAt ?? new Date().toISOString(),
    active: params.active ?? true,
  });
}

export function createSubscriptionExecution(
  params: Partial<SubscriptionExecution> & { subscriptionId: string; eventId: string; eventType: string },
): SubscriptionExecution {
  return Object.freeze({
    subscriptionId: params.subscriptionId,
    eventId: params.eventId,
    eventType: params.eventType,
    success: params.success ?? true,
    durationMs: params.durationMs ?? 0,
    error: params.error,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createSubscriptionResult(
  params: Partial<SubscriptionResult> & { publishedEvent: PublishedEvent },
): SubscriptionResult {
  const executions = params.executions ?? [];
  return Object.freeze({
    publishedEvent: params.publishedEvent,
    executions: Object.freeze([...executions]),
    totalExecutions: params.totalExecutions ?? executions.length,
    successfulExecutions:
      params.successfulExecutions ?? executions.filter((e) => e.success).length,
    failedExecutions:
      params.failedExecutions ?? executions.filter((e) => !e.success).length,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createSubscriberStatistics(params: Partial<SubscriberStatistics> = {}): SubscriberStatistics {
  return Object.freeze({
    totalSubscriptions: params.totalSubscriptions ?? 0,
    activeSubscriptions: params.activeSubscriptions ?? 0,
    totalExecutions: params.totalExecutions ?? 0,
    successfulExecutions: params.successfulExecutions ?? 0,
    failedExecutions: params.failedExecutions ?? 0,
    averageExecutionMs: params.averageExecutionMs ?? 0,
  });
}

export function createSubscriberHealth(params: Partial<SubscriberHealth> = {}): SubscriberHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    activeSubscriptionsCount: params.activeSubscriptionsCount ?? 0,
    totalExecutionsCount: params.totalExecutionsCount ?? 0,
    errorRate: params.errorRate ?? 0,
  });
}

export function createRoutingRule(
  params: Partial<RoutingRule> & { name: string; topicPattern: string },
): RoutingRule {
  return Object.freeze({
    ruleId: params.ruleId ?? `rule_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    topicPattern: params.topicPattern,
    predicate: params.predicate,
    priority: params.priority ?? EventPriority.NORMAL,
    enabled: params.enabled ?? true,
  });
}

export function createRoutingDecision(
  params: Partial<RoutingDecision> & { event: FrontendEvent; matchedRules: ReadonlyArray<RoutingRule> },
): RoutingDecision {
  const rules = params.matchedRules ?? [];
  return Object.freeze({
    decisionId: params.decisionId ?? `dec_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    event: params.event,
    matchedRules: Object.freeze([...rules]),
    matched: params.matched ?? rules.length > 0,
    evaluatedAt: params.evaluatedAt ?? new Date().toISOString(),
  });
}

export function createDispatchPolicy(params: Partial<DispatchPolicy> = {}): DispatchPolicy {
  return Object.freeze({
    policyId: params.policyId ?? `policy_default`,
    name: params.name ?? 'Default Dispatch Policy',
    stopOnFirstFailure: params.stopOnFirstFailure ?? false,
    deadLetterEnabled: params.deadLetterEnabled ?? true,
  });
}

export function createDispatchRecord(
  params: Partial<DispatchRecord> & { decision: RoutingDecision },
): DispatchRecord {
  const executions = params.executions ?? [];
  return Object.freeze({
    dispatchId: params.dispatchId ?? `dsp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    decision: params.decision,
    executions: Object.freeze([...executions]),
    success: params.success ?? (executions.length === 0 || executions.every((e) => e.success)),
    totalDurationMs: params.totalDurationMs ?? 0,
    dispatchedAt: params.dispatchedAt ?? new Date().toISOString(),
  });
}

export function createDispatchStatistics(params: Partial<DispatchStatistics> = {}): DispatchStatistics {
  return Object.freeze({
    totalDispatches: params.totalDispatches ?? 0,
    successfulDispatches: params.successfulDispatches ?? 0,
    failedDispatches: params.failedDispatches ?? 0,
    averageDispatchMs: params.averageDispatchMs ?? 0,
    deadLetterCount: params.deadLetterCount ?? 0,
  });
}

export function createDispatchHealth(params: Partial<DispatchHealth> = {}): DispatchHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    activeRulesCount: params.activeRulesCount ?? 0,
    dispatchErrorRate: params.dispatchErrorRate ?? 0,
  });
}

export function createDeadLetterRecord(
  params: Partial<DeadLetterRecord> & { event: FrontendEvent; reason: string },
): DeadLetterRecord {
  return Object.freeze({
    deadLetterId: params.deadLetterId ?? `dl_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    event: params.event,
    reason: params.reason,
    error: params.error,
    failedAt: params.failedAt ?? new Date().toISOString(),
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
    subscriberCount: params.subscriberCount,
    subscriptionCount: params.subscriptionCount,
    subscriberStatistics: params.subscriberStatistics,
    subscriberHealth: params.subscriberHealth,
    routingRules: params.routingRules ? Object.freeze([...params.routingRules]) : undefined,
    dispatchStatistics: params.dispatchStatistics,
    dispatchHealth: params.dispatchHealth,
    deadLetterCount: params.deadLetterCount,
    routingEvaluations: params.routingEvaluations,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
