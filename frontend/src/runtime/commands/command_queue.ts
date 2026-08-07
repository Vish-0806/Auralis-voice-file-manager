/**
 * Command Queue Implementation (Phase 16.6.6).
 *
 * Implements ICommandQueue managing priority queueing and FIFO ordering
 * of command execution requests with overflow capacity limits, telemetry tracking,
 * and occupancy health monitoring.
 */

import {
  CommandExecutionRequest,
  QueueDiagnostics,
  QueueEntry,
  QueueHealth,
  QueueStatistics,
  createQueueDiagnostics,
  createQueueEntry,
  createQueueHealth,
  createQueueStatistics,
} from './models';
import { CommandValidationException } from './exceptions';
import { ICommandQueue } from './interfaces';

export class CommandQueue implements ICommandQueue {
  private readonly _queue: QueueEntry[] = [];
  private readonly _capacity: number;

  private _totalInsertions = 0;
  private _totalRemovals = 0;
  private _peakSize = 0;
  private _queueTimes: number[] = [];

  constructor(capacity = 1000) {
    this._capacity = capacity;
  }

  public async queue(request: CommandExecutionRequest, priority = 0): Promise<QueueEntry> {
    if (!request) {
      throw new CommandValidationException('Queue request cannot be null or undefined.');
    }
    if (this._queue.length >= this._capacity) {
      throw new CommandValidationException(`Command queue overflow. Max capacity of ${this._capacity} exceeded.`);
    }

    const entry = createQueueEntry({
      request,
      priority,
      enqueuedAt: new Date().toISOString(),
    });

    this._queue.push(entry);
    this.sortQueue();

    this._totalInsertions++;
    this._peakSize = Math.max(this._peakSize, this._queue.length);

    return entry;
  }

  public async dequeue(): Promise<QueueEntry | undefined> {
    const entry = this._queue.shift();
    if (entry) {
      this._totalRemovals++;
      const queueDuration = Date.now() - new Date(entry.enqueuedAt).getTime();
      this._queueTimes.push(queueDuration);
      if (this._queueTimes.length > 1000) {
        this._queueTimes.shift();
      }
    }
    return entry;
  }

  public peek(): QueueEntry | undefined {
    return this._queue[0];
  }

  public queueSize(): number {
    return this._queue.length;
  }

  public clearQueue(): void {
    this._queue.length = 0;
  }

  public statistics(): QueueStatistics {
    const avgQueueTime =
      this._queueTimes.length > 0
        ? this._queueTimes.reduce((a, b) => a + b, 0) / this._queueTimes.length
        : 0;

    return createQueueStatistics({
      totalInsertions: this._totalInsertions,
      totalRemovals: this._totalRemovals,
      currentSize: this._queue.length,
      capacity: this._capacity,
      peakSize: this._peakSize,
      averageQueueTimeMs: Math.round(avgQueueTime * 100) / 100,
    });
  }

  public health(): QueueHealth {
    const occupancyRate =
      this._capacity > 0 ? Math.round((this._queue.length / this._capacity) * 100) : 0;
    const healthy = occupancyRate <= 90;

    return createQueueHealth({
      healthy,
      occupancyRate,
      message: healthy
        ? 'Command queue is operational.'
        : `Command queue warning: occupancy rate at ${occupancyRate}%.`,
    });
  }

  public diagnostics(): QueueDiagnostics {
    return createQueueDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      currentSize: this._queue.length,
    });
  }

  public clear(): void {
    this._queue.length = 0;
    this._totalInsertions = 0;
    this._totalRemovals = 0;
    this._peakSize = 0;
    this._queueTimes.length = 0;
  }

  private sortQueue(): void {
    this._queue.sort((a, b) => {
      if (b.priority !== a.priority) {
        return b.priority - a.priority;
      }
      return new Date(a.enqueuedAt).getTime() - new Date(b.enqueuedAt).getTime();
    });
  }
}
