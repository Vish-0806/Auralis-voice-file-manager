/**
 * Subscriber Registry Engine (Phase 16.4.3).
 *
 * Manages event subscriptions, subscriber registrations, handler lookups,
 * priority ordering (CRITICAL > HIGH > NORMAL > LOW), and unregistration.
 */

import {
  createEventSubscription,
  createSubscriberRegistration,
  EventPriority,
  EventSubscription,
  FrontendEvent,
  SubscriberRegistration,
} from './models';
import { EventValidationException } from './exceptions';
import { ISubscriberRegistry } from './interfaces';

export class SubscriberRegistry implements ISubscriberRegistry {
  private readonly _subscribers = new Map<string, SubscriberRegistration<any>>();

  public subscribe<T = unknown>(
    eventType: string,
    handler: (event: FrontendEvent<T>) => void | Promise<void>,
    priority: EventPriority = EventPriority.NORMAL,
  ): EventSubscription {
    const type = eventType ? eventType.trim() : '';
    if (!type) {
      throw new EventValidationException('Event type cannot be empty for subscription.');
    }
    if (typeof handler !== 'function') {
      throw new EventValidationException('Subscriber handler must be a valid function.');
    }

    const reg = createSubscriberRegistration<T>({
      eventType: type,
      handler,
      priority,
    });

    this._subscribers.set(reg.subscriptionId, reg);

    return createEventSubscription({
      subscriptionId: reg.subscriptionId,
      eventType: type,
      priority: reg.priority,
      subscribedAt: reg.subscribedAt,
      active: true,
    });
  }

  public unsubscribe(subscriptionId: string): boolean {
    const id = subscriptionId ? subscriptionId.trim() : '';
    return this._subscribers.delete(id);
  }

  public unsubscribeAll(eventType?: string): number {
    if (!eventType) {
      const count = this._subscribers.size;
      this._subscribers.clear();
      return count;
    }

    const targetType = eventType.trim();
    let removed = 0;
    for (const [id, reg] of Array.from(this._subscribers.entries())) {
      if (reg.eventType === targetType) {
        this._subscribers.delete(id);
        removed++;
      }
    }
    return removed;
  }

  public getSubscriber(subscriptionId: string): SubscriberRegistration | undefined {
    return this._subscribers.get(subscriptionId.trim());
  }

  public getSubscribers<T = unknown>(eventType: string): ReadonlyArray<SubscriberRegistration<T>> {
    const targetType = eventType ? eventType.trim() : '';
    const matching: SubscriberRegistration<T>[] = [];

    for (const reg of this._subscribers.values()) {
      if (reg.eventType === targetType && reg.active) {
        matching.push(reg as SubscriberRegistration<T>);
      }
    }

    // Sort descending by priority (higher enum number first)
    matching.sort((a, b) => b.priority - a.priority);

    return Object.freeze(matching);
  }

  public listSubscriptions(): ReadonlyArray<EventSubscription> {
    const subs: EventSubscription[] = Array.from(this._subscribers.values()).map((reg) =>
      createEventSubscription({
        subscriptionId: reg.subscriptionId,
        eventType: reg.eventType,
        priority: reg.priority,
        subscribedAt: reg.subscribedAt,
        active: reg.active,
      }),
    );
    return Object.freeze(subs);
  }

  public listSubscribers(eventType?: string): ReadonlyArray<SubscriberRegistration> {
    if (!eventType) {
      return Object.freeze(Array.from(this._subscribers.values()));
    }
    return this.getSubscribers(eventType);
  }

  public count(eventType?: string): number {
    if (!eventType) {
      return this._subscribers.size;
    }
    return this.getSubscribers(eventType).length;
  }

  public clear(): void {
    this._subscribers.clear();
  }
}
