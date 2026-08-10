import type { TelemetryRecord } from '../models/telemetry';
import { TelemetryValidationError } from '../errors/TelemetryErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class TelemetryBuffer {
  private buffer: TelemetryRecord[] = [];

  constructor(private capacity: number = 1000) {
    if (capacity <= 0) {
      throw new TelemetryValidationError('Buffer capacity must be a positive number.');
    }
  }

  public getCapacity(): number {
    return this.capacity;
  }

  public setCapacity(newCapacity: number): { evicted: TelemetryRecord[] } {
    if (newCapacity <= 0) {
      throw new TelemetryValidationError('Buffer capacity must be a positive number.');
    }
    this.capacity = newCapacity;
    const evicted: TelemetryRecord[] = [];
    while (this.buffer.length > this.capacity) {
      const item = this.buffer.shift();
      if (item) evicted.push(item);
    }
    return { evicted };
  }

  public enqueue(record: TelemetryRecord): { evicted: TelemetryRecord[] } {
    if (!record) {
      throw new TelemetryValidationError('Cannot enqueue null or undefined record.');
    }
    const evicted: TelemetryRecord[] = [];
    if (this.buffer.length >= this.capacity) {
      const countToEvict = (this.buffer.length - this.capacity) + 1;
      for (let i = 0; i < countToEvict; i++) {
        const item = this.buffer.shift();
        if (item) evicted.push(item);
      }
    }
    this.buffer.push(record);
    return { evicted };
  }

  public dequeue(limit?: number): TelemetryRecord[] {
    const count = limit !== undefined ? Math.min(limit, this.buffer.length) : this.buffer.length;
    return this.buffer.splice(0, count);
  }

  public peek(limit?: number): ReadonlyArray<TelemetryRecord> {
    const count = limit !== undefined ? Math.min(limit, this.buffer.length) : this.buffer.length;
    return freezeDeepSafe(this.buffer.slice(0, count)) as ReadonlyArray<TelemetryRecord>;
  }

  public size(): number {
    return this.buffer.length;
  }

  public clear(): void {
    this.buffer.length = 0;
  }

  public prepend(records: TelemetryRecord[]): { evicted: TelemetryRecord[] } {
    const evicted: TelemetryRecord[] = [];
    this.buffer.unshift(...records);
    while (this.buffer.length > this.capacity) {
      const item = this.buffer.shift();
      if (item) evicted.push(item);
    }
    return { evicted };
  }
}
