/**
 * Event Provider Implementation (Phase 16.4.4).
 *
 * Implements IEventProvider owning runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, capabilities reporting,
 * event registration management, event publishing, subscriber management,
 * event routing, priority dispatch, and diagnostics aggregation.
 */

import {
  createEventCapabilities,
  createEventConfiguration,
  createEventContext,
  createEventDiagnostics,
  createEventHealth,
  createEventState,
  createEventStatistics,
  DispatchHealth,
  DispatchStatistics,
  EventCapabilities,
  EventConfiguration,
  EventContext,
  EventDiagnostics,
  EventHealth,
  EventHistory,
  EventPriority,
  EventRegistration,
  EventRuntimeState,
  EventState,
  EventStatistics,
  EventSubscription,
  FrontendEvent,
  PublishedEvent,
  RoutingDecision,
  RoutingRule,
  SubscriberRegistration,
} from './models';
import { IEventProvider } from './interfaces';
import { EventRegistry } from './event_registry';
import { EventBus } from './event_bus';
import { SubscriberRegistry } from './subscriber_registry';
import { SubscriptionManager } from './subscription_manager';
import { EventRouter } from './event_router';
import { DispatchManager } from './dispatch_manager';

export class EventProvider implements IEventProvider {
  private _runtimeState: EventRuntimeState = EventRuntimeState.UNINITIALIZED;
  private readonly _config: EventConfiguration;
  private readonly _capabilities: EventCapabilities;
  private readonly _context: EventContext;

  private readonly _registry: EventRegistry;
  private readonly _subscriberRegistry: SubscriberRegistry;
  private readonly _subscriptionManager: SubscriptionManager;
  private readonly _router: EventRouter;
  private readonly _dispatchManager: DispatchManager;
  private readonly _bus: EventBus;

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: EventConfiguration,
    capabilities?: EventCapabilities,
    context?: EventContext,
    registry?: EventRegistry,
    subscriberRegistry?: SubscriberRegistry,
    subscriptionManager?: SubscriptionManager,
    router?: EventRouter,
    dispatchManager?: DispatchManager,
    bus?: EventBus,
  ) {
    this._config = config ?? createEventConfiguration();
    this._capabilities = capabilities ?? createEventCapabilities();
    this._context = context ?? createEventContext();

    this._registry = registry ?? new EventRegistry();
    this._subscriberRegistry = subscriberRegistry ?? new SubscriberRegistry();
    this._subscriptionManager = subscriptionManager ?? new SubscriptionManager();
    this._router = router ?? new EventRouter();
    this._dispatchManager =
      dispatchManager ?? new DispatchManager(this._subscriptionManager);

    this._bus =
      bus ??
      new EventBus(
        this._registry,
        this._subscriberRegistry,
        this._subscriptionManager,
        this._router,
        this._dispatchManager,
        this._config.maxQueueSize ?? 1000,
      );
  }

  public initialize(): EventHealth {
    if (
      this._runtimeState === EventRuntimeState.INITIALIZING ||
      this._runtimeState === EventRuntimeState.READY
    ) {
      return this.health();
    }

    this._runtimeState = EventRuntimeState.INITIALIZING;
    this._runtimeState = EventRuntimeState.READY;
    this._startedAt = new Date().toISOString();
    this._initializations++;

    return this.health();
  }

  public shutdown(): EventHealth {
    if (this._runtimeState === EventRuntimeState.STOPPED) {
      return this.health();
    }

    this._runtimeState = EventRuntimeState.STOPPING;
    this._runtimeState = EventRuntimeState.STOPPED;
    this._startedAt = null;
    this._shutdowns++;

    return this.health();
  }

  public restart(): EventHealth {
    this._restarts++;
    this.shutdown();
    return this.initialize();
  }

  public health(): EventHealth {
    const healthy = this._runtimeState === EventRuntimeState.READY;
    const message = healthy
      ? 'Event runtime is ready and operational.'
      : `Event runtime is in state ${this._runtimeState}.`;

    return createEventHealth({
      healthy,
      runtimeState: this._runtimeState,
      message,
    });
  }

  public statistics(): EventStatistics {
    const uptime =
      this._runtimeState === EventRuntimeState.READY && this._startedAt
        ? Math.max(0, Math.floor((Date.now() - new Date(this._startedAt).getTime()) / 1000))
        : 0;

    return createEventStatistics({
      initializations: this._initializations,
      shutdowns: this._shutdowns,
      restarts: this._restarts,
      errors: this._errors,
      uptime,
    });
  }

  public capabilities(): EventCapabilities {
    return this._capabilities;
  }

  public diagnostics(): EventDiagnostics {
    const registeredTypes = this._registry.list().map((r) => r.eventType);
    const busStats = this._bus.statistics();
    const history = this._bus.history();
    const subStats = this._subscriptionManager.statistics();
    const subHealth = this._subscriptionManager.health();
    const rules = this._router.listRules().map((r) => `${r.name} (${r.topicPattern})`);
    const dspStats = this._dispatchManager.statistics();
    const dspHealth = this._dispatchManager.health();
    const routerTelem = this._router.telemetry();

    return createEventDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      registeredEvents: registeredTypes,
      publishedEvents: busStats.publishCount,
      eventHistorySize: history.events.length,
      busStatistics: busStats,
      subscriberCount: this._subscriberRegistry.count(),
      subscriptionCount: this._subscriberRegistry.listSubscriptions().length,
      subscriberStatistics: subStats,
      subscriberHealth: subHealth,
      routingRules: rules,
      dispatchStatistics: dspStats,
      dispatchHealth: dspHealth,
      deadLetterCount: dspStats.deadLetterCount,
      routingEvaluations: routerTelem.evaluations,
      timestamp: new Date().toISOString(),
    });
  }

  public state(): EventState {
    return createEventState({
      runtimeState: this._runtimeState,
      initialized: this._runtimeState === EventRuntimeState.READY,
      startedAt: this._startedAt,
    });
  }

  public configuration(): EventConfiguration {
    return this._config;
  }

  public context(): EventContext {
    return this._context;
  }

  public registerEvent(registration: EventRegistration): void {
    this._registry.register(registration);
  }

  public unregisterEvent(eventType: string): boolean {
    return this._registry.unregister(eventType);
  }

  public containsEvent(eventType: string): boolean {
    return this._registry.contains(eventType);
  }

  public listEvents(): ReadonlyArray<EventRegistration> {
    return this._registry.list();
  }

  public publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T> {
    return this._bus.publish(eventType, payload, options);
  }

  public subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority?: EventPriority,
  ): EventSubscription {
    return this._bus.subscribe(eventType, handler, priority);
  }

  public unsubscribe(subscriptionId: string): boolean {
    return this._bus.unsubscribe(subscriptionId);
  }

  public unsubscribeAll(eventType?: string): number {
    return this._bus.unsubscribeAll(eventType);
  }

  public listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration> {
    return this._bus.listSubscribers(eventType);
  }

  public listSubscriptions(): ReadonlyArray<EventSubscription> {
    return this._bus.listSubscriptions();
  }

  public subscriberCount(eventType?: string): number {
    return this._bus.subscriberCount(eventType);
  }

  public history(): EventHistory {
    return this._bus.history();
  }

  public clearHistory(): void {
    this._bus.clearHistory();
  }

  public registerRoutingRule(rule: RoutingRule): void {
    this._router.registerRule(rule);
  }

  public removeRoutingRule(ruleId: string): boolean {
    return this._router.removeRule(ruleId);
  }

  public listRoutingRules(): ReadonlyArray<RoutingRule> {
    return this._router.listRules();
  }

  public route<T = unknown>(event: FrontendEvent<T>): RoutingDecision {
    return this._router.route(event);
  }

  public dispatchStatistics(): DispatchStatistics {
    return this._dispatchManager.statistics();
  }

  public dispatchHealth(): DispatchHealth {
    return this._dispatchManager.health();
  }
}
