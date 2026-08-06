/**
 * Event & Messaging Runtime Domain Models (Phase 16.4.6).
 *
 * Provides immutable state models, event objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, diagnostics
 * telemetry, priority enums, configuration objects, event registration definitions,
 * published event records, subscriber registrations, execution results, subscriber health,
 * routing rules, routing decisions, dispatch policies, dispatch records, dead-letter telemetry,
 * queued events, queue statistics, retry policies, retry records, replay records, acknowledgements,
 * reliability health, and certification models for the Frontend Event Runtime.
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

export enum DeliveryStatus {
  PENDING = 'PENDING',
  DELIVERED = 'DELIVERED',
  FAILED = 'FAILED',
  RETRIED = 'RETRIED',
  DEAD_LETTERED = 'DEAD_LETTERED',
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

export interface QueuedEvent<T = unknown> {
  readonly queueId: string;
  readonly event: FrontendEvent<T>;
  readonly priority: EventPriority;
  readonly enqueuedAt: string;
  readonly attemptCount: number;
  readonly status: DeliveryStatus;
}

export interface QueueStatistics {
  readonly enqueuedCount: number;
  readonly dequeuedCount: number;
  readonly currentDepth: number;
  readonly overflowCount: number;
  readonly maxCapacity: number;
}

export interface QueueHealth {
  readonly healthy: boolean;
  readonly depth: number;
  readonly capacity: number;
  readonly isOverflowed: boolean;
}

export interface QueueConfiguration {
  readonly maxCapacity: number;
  readonly dropStrategy: 'DROP_OLDEST' | 'REJECT_NEW';
}

export interface RetryPolicy {
  readonly policyId: string;
  readonly maxRetries: number;
  readonly initialDelayMs: number;
  readonly backoffMultiplier: number;
}

export interface RetryRecord {
  readonly retryId: string;
  readonly queueId: string;
  readonly eventId: string;
  readonly attempt: number;
  readonly success: boolean;
  readonly error?: string;
  readonly retriedAt: string;
}

export interface RetryStatistics {
  readonly totalRetries: number;
  readonly successfulRetries: number;
  readonly failedRetries: number;
  readonly exhaustedRetries: number;
}

export interface ReplayRecord {
  readonly replayId: string;
  readonly eventId: string;
  readonly replayedAt: string;
  readonly success: boolean;
}

export interface ReplayStatistics {
  readonly totalReplays: number;
  readonly successfulReplays: number;
  readonly failedReplays: number;
}

export interface Acknowledgement {
  readonly ackId: string;
  readonly queueId: string;
  readonly eventId: string;
  readonly status: DeliveryStatus;
  readonly acknowledgedAt: string;
}

export interface ReliabilityStatistics {
  readonly queueStats: QueueStatistics;
  readonly retryStats: RetryStatistics;
  readonly replayStats: ReplayStatistics;
  readonly acknowledgementCount: number;
}

export interface ReliabilityHealth {
  readonly healthy: boolean;
  readonly queueHealth: QueueHealth;
  readonly retryErrorRate: number;
}

export interface CertificationIssue {
  readonly issueId: string;
  readonly severity: 'INFO' | 'WARNING' | 'CRITICAL';
  readonly category: string;
  readonly message: string;
  readonly timestamp: string;
}

export interface EventCertification {
  readonly certified: boolean;
  readonly score: number;
  readonly passedChecks: number;
  readonly failedChecks: number;
  readonly certifiedAt: string;
}

export interface EventCertificationSummary {
  readonly certified: boolean;
  readonly score: number;
  readonly status: string;
  readonly certifiedAt: string;
}

export interface CertificationStatistics {
  readonly totalCertifications: number;
  readonly passedCertifications: number;
  readonly failedCertifications: number;
  readonly averageScore: number;
}

export interface CertificationHealth {
  readonly healthy: boolean;
  readonly certified: boolean;
  readonly score: number;
}

export interface CertificationReport {
  readonly certification: EventCertification;
  readonly summary: EventCertificationSummary;
  readonly issues: ReadonlyArray<CertificationIssue>;
  readonly diagnostics: EventDiagnostics;
  readonly generatedAt: string;
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
  readonly queueDepth?: number;
  readonly retryStatistics?: RetryStatistics;
  readonly replayStatistics?: ReplayStatistics;
  readonly reliabilityStatistics?: ReliabilityStatistics;
  readonly deadLetterQueueSize?: number;
  readonly certification?: EventCertification;
  readonly certificationSummary?: EventCertificationSummary;
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

export function createQueuedEvent<T = unknown>(
  params: Partial<QueuedEvent<T>> & { event: FrontendEvent<T> },
): QueuedEvent<T> {
  return Object.freeze({
    queueId: params.queueId ?? `qid_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    event: params.event,
    priority: params.priority ?? params.event.priority ?? EventPriority.NORMAL,
    enqueuedAt: params.enqueuedAt ?? new Date().toISOString(),
    attemptCount: params.attemptCount ?? 0,
    status: params.status ?? DeliveryStatus.PENDING,
  });
}

export function createQueueStatistics(params: Partial<QueueStatistics> = {}): QueueStatistics {
  return Object.freeze({
    enqueuedCount: params.enqueuedCount ?? 0,
    dequeuedCount: params.dequeuedCount ?? 0,
    currentDepth: params.currentDepth ?? 0,
    overflowCount: params.overflowCount ?? 0,
    maxCapacity: params.maxCapacity ?? 1000,
  });
}

export function createQueueHealth(params: Partial<QueueHealth> = {}): QueueHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    depth: params.depth ?? 0,
    capacity: params.capacity ?? 1000,
    isOverflowed: params.isOverflowed ?? false,
  });
}

export function createQueueConfiguration(params: Partial<QueueConfiguration> = {}): QueueConfiguration {
  return Object.freeze({
    maxCapacity: params.maxCapacity ?? 1000,
    dropStrategy: params.dropStrategy ?? 'DROP_OLDEST',
  });
}

export function createRetryPolicy(params: Partial<RetryPolicy> = {}): RetryPolicy {
  return Object.freeze({
    policyId: params.policyId ?? 'default_retry_policy',
    maxRetries: params.maxRetries ?? 3,
    initialDelayMs: params.initialDelayMs ?? 100,
    backoffMultiplier: params.backoffMultiplier ?? 2.0,
  });
}

export function createRetryRecord(
  params: Partial<RetryRecord> & { queueId: string; eventId: string; attempt: number },
): RetryRecord {
  return Object.freeze({
    retryId: params.retryId ?? `ret_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    queueId: params.queueId,
    eventId: params.eventId,
    attempt: params.attempt,
    success: params.success ?? false,
    error: params.error,
    retriedAt: params.retriedAt ?? new Date().toISOString(),
  });
}

export function createRetryStatistics(params: Partial<RetryStatistics> = {}): RetryStatistics {
  return Object.freeze({
    totalRetries: params.totalRetries ?? 0,
    successfulRetries: params.successfulRetries ?? 0,
    failedRetries: params.failedRetries ?? 0,
    exhaustedRetries: params.exhaustedRetries ?? 0,
  });
}

export function createReplayRecord(
  params: Partial<ReplayRecord> & { eventId: string },
): ReplayRecord {
  return Object.freeze({
    replayId: params.replayId ?? `rpl_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    eventId: params.eventId,
    replayedAt: params.replayedAt ?? new Date().toISOString(),
    success: params.success ?? true,
  });
}

export function createReplayStatistics(params: Partial<ReplayStatistics> = {}): ReplayStatistics {
  return Object.freeze({
    totalReplays: params.totalReplays ?? 0,
    successfulReplays: params.successfulReplays ?? 0,
    failedReplays: params.failedReplays ?? 0,
  });
}

export function createAcknowledgement(
  params: Partial<Acknowledgement> & { queueId: string; eventId: string },
): Acknowledgement {
  return Object.freeze({
    ackId: params.ackId ?? `ack_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    queueId: params.queueId,
    eventId: params.eventId,
    status: params.status ?? DeliveryStatus.DELIVERED,
    acknowledgedAt: params.acknowledgedAt ?? new Date().toISOString(),
  });
}

export function createReliabilityStatistics(params: Partial<ReliabilityStatistics> = {}): ReliabilityStatistics {
  return Object.freeze({
    queueStats: params.queueStats ?? createQueueStatistics(),
    retryStats: params.retryStats ?? createRetryStatistics(),
    replayStats: params.replayStats ?? createReplayStatistics(),
    acknowledgementCount: params.acknowledgementCount ?? 0,
  });
}

export function createReliabilityHealth(params: Partial<ReliabilityHealth> = {}): ReliabilityHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    queueHealth: params.queueHealth ?? createQueueHealth(),
    retryErrorRate: params.retryErrorRate ?? 0,
  });
}

export function createCertificationIssue(
  params: Partial<CertificationIssue> & { category: string; message: string },
): CertificationIssue {
  return Object.freeze({
    issueId: params.issueId ?? `issue_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    severity: params.severity ?? 'INFO',
    category: params.category,
    message: params.message,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createEventCertification(params: Partial<EventCertification> = {}): EventCertification {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    passedChecks: params.passedChecks ?? 10,
    failedChecks: params.failedChecks ?? 0,
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createEventCertificationSummary(params: Partial<EventCertificationSummary> = {}): EventCertificationSummary {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    status: params.status ?? 'PASSED',
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createCertificationStatistics(params: Partial<CertificationStatistics> = {}): CertificationStatistics {
  return Object.freeze({
    totalCertifications: params.totalCertifications ?? 0,
    passedCertifications: params.passedCertifications ?? 0,
    failedCertifications: params.failedCertifications ?? 0,
    averageScore: params.averageScore ?? 100,
  });
}

export function createCertificationHealth(params: Partial<CertificationHealth> = {}): CertificationHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    certified: params.certified ?? true,
    score: params.score ?? 100,
  });
}

export function createCertificationReport(
  params: Partial<CertificationReport> & { diagnostics: EventDiagnostics },
): CertificationReport {
  const issues = params.issues ?? [];
  const cert = params.certification ?? createEventCertification();
  const summary = params.summary ?? createEventCertificationSummary({ certified: cert.certified, score: cert.score });

  return Object.freeze({
    certification: cert,
    summary,
    issues: Object.freeze([...issues]),
    diagnostics: params.diagnostics,
    generatedAt: params.generatedAt ?? new Date().toISOString(),
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
    queueDepth: params.queueDepth,
    retryStatistics: params.retryStatistics,
    replayStatistics: params.replayStatistics,
    reliabilityStatistics: params.reliabilityStatistics,
    deadLetterQueueSize: params.deadLetterQueueSize,
    certification: params.certification,
    certificationSummary: params.certificationSummary,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
