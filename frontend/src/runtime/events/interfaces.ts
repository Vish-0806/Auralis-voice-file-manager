/**
 * Event & Messaging Runtime Interfaces (Phase 16.4.4).
 *
 * Defines contracts for IEventRegistry, IEventBus, ISubscriberRegistry, ISubscriptionManager,
 * IEventRouter, IDispatchManager, IEventProvider, and IEventRuntime.
 */

import {
  DeadLetterRecord,
  DispatchHealth,
  DispatchRecord,
  DispatchStatistics,
  EventBusHealth,
  EventBusStatistics,
  EventCapabilities,
  EventConfiguration,
  EventContext,
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
  RoutingDecision,
  RoutingRule,
  SubscriberHealth,
  SubscriberRegistration,
  SubscriberStatistics,
  SubscriptionResult,
} from './models';

export interface IEventRegistry {
  register(registration: EventRegistration): void;
  unregister(eventType: string): boolean;
  contains(eventType: string): boolean;
  get(eventType: string): EventRegistration | undefined;
  list(): ReadonlyArray<EventRegistration>;
  count(): number;
  clear(): void;
}

export interface ISubscriberRegistry {
  subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority?: EventPriority,
  ): EventSubscription;
  unsubscribe(subscriptionId: string): boolean;
  unsubscribeAll(eventType?: string): number;
  getSubscriber(subscriptionId: string): SubscriberRegistration | undefined;
  getSubscribers<T = unknown>(eventType: string): ReadonlyArray<SubscriberRegistration<T>>;
  listSubscriptions(): ReadonlyArray<EventSubscription>;
  listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration>;
  count(eventType?: string): number;
  clear(): void;
}

export interface ISubscriptionManager {
  executeSubscribers<T = unknown>(
    publishedEvent: PublishedEvent<T>,
    subscribers: ReadonlyArray<SubscriberRegistration<T>>,
  ): SubscriptionResult;
  statistics(): SubscriberStatistics;
  health(): SubscriberHealth;
}

export interface IEventRouter {
  registerRule(rule: RoutingRule): void;
  removeRule(ruleId: string): boolean;
  getRule(ruleId: string): RoutingRule | undefined;
  listRules(): ReadonlyArray<RoutingRule>;
  route<T = unknown>(event: FrontendEvent<T>): RoutingDecision;
  clearRules(): void;
}

export interface IDispatchManager {
  dispatch<T = unknown>(
    decision: RoutingDecision,
    subscribers: ReadonlyArray<SubscriberRegistration<T>>,
  ): DispatchRecord;
  listDeadLetters(): ReadonlyArray<DeadLetterRecord>;
  clearDeadLetters(): void;
  statistics(): DispatchStatistics;
  health(): DispatchHealth;
}

export interface IEventBus {
  publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T>;
  subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority?: EventPriority,
  ): EventSubscription;
  unsubscribe(subscriptionId: string): boolean;
  unsubscribeAll(eventType?: string): number;
  listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration>;
  listSubscriptions(): ReadonlyArray<EventSubscription>;
  subscriberCount(eventType?: string): number;
  history(): EventHistory;
  clearHistory(): void;
  statistics(): EventBusStatistics;
  health(): EventBusHealth;
}

export interface IEventProvider {
  initialize(): EventHealth;
  shutdown(): EventHealth;
  restart(): EventHealth;
  health(): EventHealth;
  statistics(): EventStatistics;
  capabilities(): EventCapabilities;
  diagnostics(): EventDiagnostics;
  state(): EventState;
  configuration(): EventConfiguration;
  context(): EventContext;

  registerEvent(registration: EventRegistration): void;
  unregisterEvent(eventType: string): boolean;
  containsEvent(eventType: string): boolean;
  listEvents(): ReadonlyArray<EventRegistration>;
  publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T>;
  subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority?: EventPriority,
  ): EventSubscription;
  unsubscribe(subscriptionId: string): boolean;
  unsubscribeAll(eventType?: string): number;
  listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration>;
  listSubscriptions(): ReadonlyArray<EventSubscription>;
  subscriberCount(eventType?: string): number;
  history(): EventHistory;
  clearHistory(): void;

  registerRoutingRule(rule: RoutingRule): void;
  removeRoutingRule(ruleId: string): boolean;
  listRoutingRules(): ReadonlyArray<RoutingRule>;
  route<T = unknown>(event: FrontendEvent<T>): RoutingDecision;
  dispatchStatistics(): DispatchStatistics;
  dispatchHealth(): DispatchHealth;
}

export interface IEventRuntime {
  initialize(): EventHealth;
  shutdown(): EventHealth;
  restart(): EventHealth;
  provider(): IEventProvider;
  health(): EventHealth;
  statistics(): EventStatistics;
  capabilities(): EventCapabilities;
  diagnostics(): EventDiagnostics;
  state(): EventState;

  registerEvent(registration: EventRegistration): void;
  unregisterEvent(eventType: string): boolean;
  containsEvent(eventType: string): boolean;
  listEvents(): ReadonlyArray<EventRegistration>;
  publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T>;
  subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority?: EventPriority,
  ): EventSubscription;
  unsubscribe(subscriptionId: string): boolean;
  unsubscribeAll(eventType?: string): number;
  listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration>;
  listSubscriptions(): ReadonlyArray<EventSubscription>;
  subscriberCount(eventType?: string): number;
  history(): EventHistory;
  clearHistory(): void;

  registerRoutingRule(rule: RoutingRule): void;
  removeRoutingRule(ruleId: string): boolean;
  listRoutingRules(): ReadonlyArray<RoutingRule>;
  route<T = unknown>(event: FrontendEvent<T>): RoutingDecision;
  dispatchStatistics(): DispatchStatistics;
  dispatchHealth(): DispatchHealth;
}
