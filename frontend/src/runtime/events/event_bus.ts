/**
 * Event Bus Implementation (Phase 16.4.2).
 *
 * Implements IEventBus managing event publication, registration validation, sequence numbering,
 * bounded event history tracking, payload telemetry, and health reporting.
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
  PublishedEvent,
} from './models';
import { EventValidationException } from './exceptions';
import { IEventBus, IEventRegistry } from './interfaces';

export class EventBus implements IEventBus {
  private readonly _registry: IEventRegistry;
  private readonly _maxHistorySize: number;

  private readonly _history: PublishedEvent[] = [];
  private _sequenceNumber = 0;

  private _publishCount = 0;
  private _failedPublishes = 0;
  private _totalPayloadBytes = 0;

  constructor(registry: IEventRegistry, maxHistorySize = 1000) {
    this._registry = registry;
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

    return published;
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
      return 100; // Fallback estimate
    }
  }
}
