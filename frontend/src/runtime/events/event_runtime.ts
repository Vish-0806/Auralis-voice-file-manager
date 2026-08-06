/**
 * Event Runtime Coordinator Implementation (Phase 16.4.5).
 *
 * Implements IEventRuntime acting as central coordinator delegating to IEventProvider.
 */

import {
  Acknowledgement,
  DeadLetterRecord,
  DeliveryStatus,
  DispatchHealth,
  DispatchStatistics,
  EventCapabilities,
  EventDiagnostics,
  EventHealth,
  EventHistory,
  EventPriority,
  EventRegistration,
  EventState,
  EventStatistics,
  EventSubscription,
  FrontendEvent,
  PublishedEvent,
  QueuedEvent,
  ReplayRecord,
  RoutingDecision,
  RoutingRule,
  SubscriberRegistration,
} from './models';
import { IEventProvider, IEventRuntime } from './interfaces';
import { EventProvider } from './event_provider';

export class EventRuntime implements IEventRuntime {
  private readonly _provider: IEventProvider;

  constructor(provider?: IEventProvider) {
    this._provider = provider ?? new EventProvider();
  }

  public initialize(): EventHealth {
    return this._provider.initialize();
  }

  public shutdown(): EventHealth {
    return this._provider.shutdown();
  }

  public restart(): EventHealth {
    return this._provider.restart();
  }

  public provider(): IEventProvider {
    return this._provider;
  }

  public health(): EventHealth {
    return this._provider.health();
  }

  public statistics(): EventStatistics {
    return this._provider.statistics();
  }

  public capabilities(): EventCapabilities {
    return this._provider.capabilities();
  }

  public diagnostics(): EventDiagnostics {
    return this._provider.diagnostics();
  }

  public state(): EventState {
    return this._provider.state();
  }

  public registerEvent(registration: EventRegistration): void {
    this._provider.registerEvent(registration);
  }

  public unregisterEvent(eventType: string): boolean {
    return this._provider.unregisterEvent(eventType);
  }

  public containsEvent(eventType: string): boolean {
    return this._provider.containsEvent(eventType);
  }

  public listEvents(): ReadonlyArray<EventRegistration> {
    return this._provider.listEvents();
  }

  public publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T> {
    return this._provider.publish(eventType, payload, options);
  }

  public subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority?: EventPriority,
  ): EventSubscription {
    return this._provider.subscribe(eventType, handler, priority);
  }

  public unsubscribe(subscriptionId: string): boolean {
    return this._provider.unsubscribe(subscriptionId);
  }

  public unsubscribeAll(eventType?: string): number {
    return this._provider.unsubscribeAll(eventType);
  }

  public listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration> {
    return this._provider.listSubscribers(eventType);
  }

  public listSubscriptions(): ReadonlyArray<EventSubscription> {
    return this._provider.listSubscriptions();
  }

  public subscriberCount(eventType?: string): number {
    return this._provider.subscriberCount(eventType);
  }

  public history(): EventHistory {
    return this._provider.history();
  }

  public clearHistory(): void {
    this._provider.clearHistory();
  }

  public registerRoutingRule(rule: RoutingRule): void {
    this._provider.registerRoutingRule(rule);
  }

  public removeRoutingRule(ruleId: string): boolean {
    return this._provider.removeRoutingRule(ruleId);
  }

  public listRoutingRules(): ReadonlyArray<RoutingRule> {
    return this._provider.listRoutingRules();
  }

  public route<T = unknown>(event: FrontendEvent<T>): RoutingDecision {
    return this._provider.route(event);
  }

  public dispatchStatistics(): DispatchStatistics {
    return this._provider.dispatchStatistics();
  }

  public dispatchHealth(): DispatchHealth {
    return this._provider.dispatchHealth();
  }

  public enqueue<T = unknown>(event: FrontendEvent<T>): QueuedEvent<T> {
    return this._provider.enqueue(event);
  }

  public dequeue<T = unknown>(): QueuedEvent<T> | undefined {
    return this._provider.dequeue<T>();
  }

  public peek<T = unknown>(): QueuedEvent<T> | undefined {
    return this._provider.peek<T>();
  }

  public queueSize(): number {
    return this._provider.queueSize();
  }

  public retry(queueId: string): boolean {
    return this._provider.retry(queueId);
  }

  public replay(filter?: (evt: PublishedEvent) => boolean): ReadonlyArray<ReplayRecord> {
    return this._provider.replay(filter);
  }

  public acknowledge(queueId: string, status = DeliveryStatus.DELIVERED): Acknowledgement {
    return this._provider.acknowledge(queueId, status);
  }

  public deadLetters(): ReadonlyArray<DeadLetterRecord> {
    return this._provider.deadLetters();
  }

  public clearDeadLetters(): void {
    this._provider.clearDeadLetters();
  }
}
