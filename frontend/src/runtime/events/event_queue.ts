/**
 * Event Queue Engine (Phase 16.4.5).
 *
 * Implements IEventQueue providing priority queue ordering (CRITICAL > HIGH > NORMAL > LOW)
 * with FIFO ordering within equal priority levels, bounded capacity, overflow management, and statistics.
 */

import {
  createQueueConfiguration,
  createQueueHealth,
  createQueueStatistics,
  createQueuedEvent,
  FrontendEvent,
  QueuedEvent,
  QueueConfiguration,
  QueueHealth,
  QueueStatistics,
} from './models';
import { EventProviderException } from './exceptions';
import { IEventQueue } from './interfaces';

export class EventQueue implements IEventQueue {
  private readonly _config: QueueConfiguration;
  private readonly _items: QueuedEvent[] = [];

  private _enqueuedCount = 0;
  private _dequeuedCount = 0;
  private _overflowCount = 0;

  constructor(config?: QueueConfiguration) {
    this._config = config ?? createQueueConfiguration();
  }

  public enqueue<T = unknown>(event: FrontendEvent<T>): QueuedEvent<T> {
    if (!event) {
      throw new EventProviderException('Cannot enqueue null or undefined event.');
    }

    if (this._items.length >= this._config.maxCapacity) {
      this._overflowCount++;
      if (this._config.dropStrategy === 'DROP_OLDEST') {
        // Find lowest priority item to drop (from the end of sorted items)
        this._items.pop();
      } else {
        throw new EventProviderException('Event Queue capacity exceeded.');
      }
    }

    const queued = createQueuedEvent<T>({ event });
    this._enqueuedCount++;

    // Insert maintaining priority order descending (higher enum value first), FIFO within priority
    let inserted = false;
    for (let i = 0; i < this._items.length; i++) {
      if (queued.priority > this._items[i].priority) {
        this._items.splice(i, 0, queued);
        inserted = true;
        break;
      }
    }
    if (!inserted) {
      this._items.push(queued);
    }

    return queued;
  }

  public dequeue<T = unknown>(): QueuedEvent<T> | undefined {
    if (this._items.length === 0) return undefined;
    const item = this._items.shift();
    if (item) {
      this._dequeuedCount++;
    }
    return item as QueuedEvent<T> | undefined;
  }

  public peek<T = unknown>(): QueuedEvent<T> | undefined {
    if (this._items.length === 0) return undefined;
    return this._items[0] as QueuedEvent<T> | undefined;
  }

  public size(): number {
    return this._items.length;
  }

  public clear(): void {
    this._items.length = 0;
  }

  public statistics(): QueueStatistics {
    return createQueueStatistics({
      enqueuedCount: this._enqueuedCount,
      dequeuedCount: this._dequeuedCount,
      currentDepth: this._items.length,
      overflowCount: this._overflowCount,
      maxCapacity: this._config.maxCapacity,
    });
  }

  public health(): QueueHealth {
    const isOverflowed = this._overflowCount > 0;
    return createQueueHealth({
      healthy: !isOverflowed && this._items.length < this._config.maxCapacity,
      depth: this._items.length,
      capacity: this._config.maxCapacity,
      isOverflowed,
    });
  }
}
