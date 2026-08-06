/**
 * Event Bus Implementation (Phase 16.4.4).
 *
 * Implements IEventBus managing event publication, registration validation, sequence numbering,
 * bounded event history tracking, routing evaluation, and dispatch execution management.
 */

import {
  createEventBusHealth,
  createEventBusStatistics,
  createEventHistory,
  createFrontendEvent,
  createPublishedEvent,
  EventBusHealth,
  EventBusStatistics,
  EventHistory,
  EventPriority,
  EventSubscription,
  FrontendEvent,
  PublishedEvent,
  SubscriberRegistration,
} from './models';
import { EventValidationException } from './exceptions';
import {
  IDispatchManager,
  IEventBus,
  IEventRegistry,
  IEventRouter,
  ISubscriberRegistry,
  ISubscriptionManager,
} from './interfaces';
import { SubscriberRegistry } from './subscriber_registry';
import { SubscriptionManager } from './subscription_manager';
import { EventRouter } from './event_router';
import { DispatchManager } from './dispatch_manager';

export class EventBus implements IEventBus {
  private readonly _registry: IEventRegistry;
  private readonly _subscriberRegistry: ISubscriberRegistry;
  private readonly _subscriptionManager: ISubscriptionManager;
  private readonly _router: IEventRouter;
  private readonly _dispatchManager: IDispatchManager;
  private readonly _maxHistorySize: number;

  private readonly _history: PublishedEvent[] = [];
  private _sequenceNumber = 0;

  private _publishCount = 0;
  private _failedPublishes = 0;
  private _totalPayloadBytes = 0;

  constructor(
    registry: IEventRegistry,
    subscriberRegistry?: ISubscriberRegistry,
    subscriptionManager?: ISubscriptionManager,
    router?: IEventRouter,
    dispatchManager?: IDispatchManager,
    maxHistorySize = 1000,
  ) {
    this._registry = registry;
    this._subscriberRegistry = subscriberRegistry ?? new SubscriberRegistry();
    this._subscriptionManager = subscriptionManager ?? new SubscriptionManager();
    this._router = router ?? new EventRouter();
    this._dispatchManager =
      dispatchManager ?? new DispatchManager(this._subscriptionManager);
    this._maxHistorySize = maxHistorySize;
  }

  public publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T> {
    const type = eventType ? eventType.trim() : '';

    if (!this._registry.contains(type)) {
      this._failedPublishes++;
      throw new EventValidationException(`Event type '${type}' is not registered on the Event Bus.`);
    }

    const reg = this._registry.get(type);
    const priority = options?.priority ?? reg?.priority ?? EventPriority.NORMAL;

    const event = createFrontendEvent<T>({
      eventType: type,
      payload,
      priority,
      source: options?.source,
      correlationId: options?.correlationId,
    });

    this._sequenceNumber++;
    this._publishCount++;

    const published = createPublishedEvent<T>({
      event,
      sequenceNumber: this._sequenceNumber,
    });

    this._history.push(published);
    if (this._history.length > this._maxHistorySize) {
      this._history.shift();
    }

    this._totalPayloadBytes += this.estimatePayloadSize(payload);

    // Event Routing & Priority Dispatch Pipeline
    const decision = this._router.route(event);
    const subscribers = this._subscriberRegistry.getSubscribers<T>(type);

    this._dispatchManager.dispatch(decision, subscribers);

    return published;
  }

  public subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority?: EventPriority,
  ): EventSubscription {
    return this._subscriberRegistry.subscribe(eventType, handler, priority);
  }

  public unsubscribe(subscriptionId: string): boolean {
    return this._subscriberRegistry.unsubscribe(subscriptionId);
  }

  public unsubscribeAll(eventType?: string): number {
    return this._subscriberRegistry.unsubscribeAll(eventType);
  }

  public listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration> {
    return this._subscriberRegistry.listSubscribers(eventType);
  }

  public listSubscriptions(): ReadonlyArray<EventSubscription> {
    return this._subscriberRegistry.listSubscriptions();
  }

  public subscriberCount(eventType?: string): number {
    return this._subscriberRegistry.count(eventType);
  }

  public history(): EventHistory {
    return createEventHistory({
      events: [...this._history],
      totalPublished: this._publishCount,
      timestamp: new Date().toISOString(),
    });
  }

  public clearHistory(): void {
    this._history.length = 0;
  }

  public statistics(): EventBusStatistics {
    const avgSize = this._publishCount > 0 ? Math.round(this._totalPayloadBytes / this._publishCount) : 0;
    return createEventBusStatistics({
      publishCount: this._publishCount,
      historyCount: this._history.length,
      failedPublishes: this._failedPublishes,
      averagePayloadSize: avgSize,
    });
  }

  public health(): EventBusHealth {
    return createEventBusHealth({
      healthy: true,
      registeredEventTypes: this._registry.count(),
      totalPublishedEvents: this._publishCount,
    });
  }

  private estimatePayloadSize(payload: unknown): number {
    if (payload === undefined || payload === null) return 0;
    try {
      return JSON.stringify(payload).length;
    } catch {
      return 100;
    }
  }
}
